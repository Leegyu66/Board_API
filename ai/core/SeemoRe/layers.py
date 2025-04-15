import torch

from torch import nn

import torch.nn.functional as F

from typing import List, Optional
from einops.layers.torch import Rearrange


def channel_shuffle(x, groups: int = 2):
    bat_size, channels, w, h = x.shape
    group_c = channels // groups
    x = x.view(bat_size, groups, group_c, w, h)
    x = torch.transpose(x, 1, 2).contiguous()
    x = x.view(bat_size, -1, w, h)
    return x

#############################
# Components
#############################    
class ResGroup(nn.Module):
    def __init__(self,
                 in_ch: int,
                 num_experts: int,
                 global_kernel_size: int = 11,
                 lr_space: int = 1,
                 topk: int = 2,
                 recursive: int = 2,
                 use_shuffle: bool = False):
        super().__init__()
        
        self.local_block = RME(in_ch=in_ch, 
                               num_experts=num_experts, 
                               use_shuffle=use_shuffle, 
                               lr_space=lr_space, 
                               topk=topk, 
                               recursive=recursive)
        self.global_block = SME(in_ch=in_ch, 
                                kernel_size=global_kernel_size)
        
    def forward(self, x: torch.Tensor) -> torch.Tensor:
        x = self.local_block(x)
        x = self.global_block(x)
        return x



#############################
# Global Block
#############################
class SME(nn.Module):
    def __init__(self,
                 in_ch: int,
                 kernel_size: int = 11):
        super().__init__()
        
        self.norm_1 = LayerNorm(in_ch, data_format='channels_first')
        self.block = StripedConvFormer(in_ch=in_ch, kernel_size=kernel_size)
    
        self.norm_2 = LayerNorm(in_ch, data_format='channels_first')
        self.ffn = GatedFFN(in_ch, mlp_ratio=2, kernel_size=3, act_layer=nn.GELU())
        
    def forward(self, x: torch.Tensor) -> torch.Tensor:
        x = self.block(self.norm_1(x)) + x
        x = self.ffn(self.norm_2(x)) + x
        return x

    
    

class StripedConvFormer(nn.Module):
    def __init__(self,
                 in_ch: int,
                 kernel_size: int):
        super().__init__()
        self.in_ch = in_ch
        self.kernel_size = kernel_size
        self.padding = kernel_size // 2
        
        self.proj = nn.Conv2d(in_ch, in_ch, kernel_size=1, padding=0)
        self.to_qv = nn.Sequential(
            nn.Conv2d(in_ch, in_ch * 2, kernel_size=1, padding=0),
            nn.GELU(),
        )

        self.attn = StripedConv2d(in_ch, kernel_size=kernel_size, depthwise=True)
    
    def forward(self, x: torch.Tensor) -> torch.Tensor:
        q, v = self.to_qv(x).chunk(2, dim=1)
        q = self.attn(q)
        x = self.proj(q * v)
        return x
    
    
    
#############################
# Local Blocks
#############################
class RME(nn.Module):
    def __init__(self,
                 in_ch: int,
                 num_experts: int,
                 topk: int,
                 lr_space: int = 1,
                 recursive: int = 2,
                 use_shuffle: bool = False,):
        super().__init__()
        
        self.norm_1 = LayerNorm(in_ch, data_format='channels_first')
        self.block = MoEBlock(in_ch=in_ch, num_experts=num_experts, topk=topk, use_shuffle=use_shuffle, recursive=recursive, lr_space=lr_space,)
        
        self.norm_2 = LayerNorm(in_ch, data_format='channels_first')
        self.ffn = GatedFFN(in_ch, mlp_ratio=2, kernel_size=3, act_layer=nn.GELU())
        
    def forward(self, x: torch.Tensor) -> torch.Tensor:
        x = self.block(self.norm_1(x)) + x
        x = self.ffn(self.norm_2(x)) + x
        return x



#################
# MoE Layer
#################
class MoEBlock(nn.Module):
    def __init__(self,
                 in_ch: int,
                 num_experts: int,
                 topk: int,
                 use_shuffle: bool = False,
                 lr_space: str = "linear",
                 recursive: int = 2):
        super().__init__()
        self.use_shuffle = use_shuffle
        self.recursive = recursive
        
        self.conv_1 = nn.Sequential(
            nn.Conv2d(in_ch, in_ch, kernel_size=3, padding=1),
            nn.GELU(),
            nn.Conv2d(in_ch, 2*in_ch, kernel_size=1, padding=0)
        )
        
        self.agg_conv = nn.Sequential(
            nn.Conv2d(in_ch, in_ch, kernel_size=4, stride=4, groups=in_ch),
            nn.GELU())
        
        self.conv = nn.Sequential(
            nn.Conv2d(in_ch, in_ch, kernel_size=3, stride=1, padding=1, groups=in_ch),
            nn.Conv2d(in_ch, in_ch, kernel_size=1, padding=0)
        )
        
        self.conv_2 = nn.Sequential(
            StripedConv2d(in_ch, kernel_size=3, depthwise=True),
            nn.GELU())
        
        if lr_space == "linear":
            grow_func = lambda i: i+2
        elif lr_space == "exp":
            grow_func = lambda i: 2**(i+1)
        elif lr_space == "double":
            grow_func = lambda i: 2*i+2
        else:
            raise NotImplementedError(f"lr_space {lr_space} not implemented")
            
        self.moe_layer = MoELayer(
            experts=[Expert(in_ch=in_ch, low_dim=grow_func(i)) for i in range(num_experts)], # add here multiple of 2 as low_dim
            gate=Router(in_ch=in_ch, num_experts=num_experts),
            num_expert=topk,
        )
        
        self.proj = nn.Conv2d(in_ch, in_ch, kernel_size=1, padding=0)
        
    def calibrate(self, x: torch.Tensor) -> torch.Tensor:
        b, c, h, w = x.shape
        res = x
        
        for _ in range(self.recursive):
            x = self.agg_conv(x)
        x = self.conv(x)
        x = F.interpolate(x, size=(h, w), mode="bilinear", align_corners=False)
        return res + x
    
    def forward(self, x: torch.Tensor) -> torch.Tensor:
        x = self.conv_1(x)
        
        if self.use_shuffle:
            x = channel_shuffle(x, groups=2)
        x, k = torch.chunk(x, chunks=2, dim=1)
        
        x = self.conv_2(x)
        k = self.calibrate(k)
        
        x = self.moe_layer(x, k)
        x = self.proj(x)
        return x 
    
    
# class MoELayer(nn.Module):
#     def __init__(self, experts: List[nn.Module], gate: nn.Module, num_expert: int = 1):
#         super().__init__()
#         assert len(experts) > 0
#         self.experts = nn.ModuleList(experts)
#         self.gate = gate
#         self.num_expert = num_expert
        
#     def forward(self, inputs: torch.Tensor, k: torch.Tensor):
#         out = self.gate(inputs)
#         weights = F.softmax(out, dim=1, dtype=torch.float).to(inputs.dtype)
#         topk_weights, topk_experts = torch.topk(weights, self.num_expert)
#         out = inputs.clone()
        
#         if self.training:
#             exp_weights = torch.zeros_like(weights)
#             exp_weights.scatter_(1, topk_experts, weights.gather(1, topk_experts))
#             for i, expert in enumerate(self.experts):
#                 out += expert(inputs, k) * exp_weights[:, i:i+1, None, None]
#         else:       
#             selected_experts = [self.experts[i] for i in topk_experts.squeeze(dim=0)]
#             for i, expert in enumerate(selected_experts):
#                 out += expert(inputs, k) * topk_weights[:, i:i+1, None, None]
                   
#         return out
    
class MoELayer(nn.Module):
    def __init__(self, experts: List[nn.Module], gate: nn.Module, num_expert: int = 1):
        super().__init__()
        # torch.jit.script 는 모듈 리스트의 동적 생성을 추적하기 어려워 할 수 있으므로,
        # 리스트가 비어있지 않음을 보장하는 것이 좋습니다.
        if not experts: # JIT 호환성을 위해 len(experts) > 0 대신 사용
             raise ValueError("Expert list cannot be empty")
        self.experts = nn.ModuleList(experts)
        self.gate = gate
        self.num_expert = num_expert # 선택할 expert의 수 (k)
        # JIT는 클래스 멤버의 타입을 추론해야 하므로, 명시적인 타입 힌트가 도움이 될 수 있습니다.
        # 하지만 여기서는 num_expert가 int임이 명확합니다.
        
    def forward(self, inputs: torch.Tensor, k: torch.Tensor) -> torch.Tensor: # k의 사용처가 불분명하지만 일단 유지
        # 입력 타입 힌트 추가
        batch_size, channels, height, width = inputs.shape # 입력 형태 가정 (예: 이미지)

        gate_out = self.gate(inputs)
        # F.softmax의 dtype 인자를 JIT가 잘 처리하도록 명시적 형변환 사용 가능성 고려
        weights = F.softmax(gate_out, dim=1, dtype=torch.float).to(inputs.dtype) # Shape: [B, num_total_experts]

        # torch.topk는 JIT에서 잘 지원됩니다.
        # topk_weights: [B, num_expert], topk_experts (indices): [B, num_expert]
        topk_weights, topk_experts_indices = torch.topk(weights, self.num_expert, dim=1)

        # 최종 출력을 저장할 텐서. 원본 코드는 inputs.clone() 후 덧셈.
        # JIT 호환성을 위해 clone 대신 zeros로 초기화하고 마지막에 더하는 방식도 고려 가능하나,
        # clone 후 덧셈도 일반적으로는 괜찮습니다.
        out = inputs.clone() # Shape: [B, C, H, W]
        
        if self.training:
            # training 부분은 그대로 둡니다. (enumerate 사용으로 JIT 호환 가능성 높음)
            exp_weights = torch.zeros_like(weights)
            # scatter_ 와 gather 는 JIT 호환 가능
            exp_weights.scatter_(1, topk_experts_indices, weights.gather(1, topk_experts_indices))
            # enumerate 는 JIT 호환 가능
            for i, expert in enumerate(self.experts):
                # 슬라이싱 [:, i:i+1, None, None] 도 JIT 호환 가능
                out += expert(inputs, k) * exp_weights[:, i:i+1, None, None]
        else: # Inference 모드
            # --- JIT 호환 버전 시작 ---
            
            # 1. 모든 expert의 출력을 계산합니다.
            #    expert 모듈들이 동일한 출력 shape를 가진다고 가정합니다.
            all_expert_outputs : List[torch.Tensor] = []
            # ModuleList 순회는 JIT 호환 가능
            for expert_module in self.experts:
                # expert 모듈이 inputs와 k를 받는다고 가정
                all_expert_outputs.append(expert_module(inputs, k))

            # 2. 출력들을 하나의 텐서로 합칩니다. (dim=1 에 num_total_experts 차원 추가)
            # Shape: [B, num_total_experts, C, H, W]
            stacked_outputs = torch.stack(all_expert_outputs, dim=1)

            # 3. torch.gather를 사용하여 topk 인덱스에 해당하는 출력을 선택합니다.
            #    gather를 위해 topk_experts_indices의 차원을 맞춰줘야 합니다.
            #    indices shape: [B, num_expert] -> [B, num_expert, C, H, W]
            idx = topk_experts_indices.unsqueeze(-1).unsqueeze(-1).unsqueeze(-1) # Shape: [B, num_expert, 1, 1, 1]
            # 입력 shape에서 C, H, W 가져오기 (JIT는 텐서 shape 접근 지원)
            C, H, W = inputs.shape[1:] # 또는 stacked_outputs.shape[2:]
            idx_expanded = idx.expand(batch_size, self.num_expert, C, H, W)

            # dim=1 (num_total_experts 차원)을 기준으로 선택
            # selected_outputs shape: [B, num_expert, C, H, W]
            selected_outputs = torch.gather(stacked_outputs, 1, idx_expanded)

            # 4. topk_weights의 차원을 맞춰 가중치를 곱합니다.
            #    weights shape: [B, num_expert] -> [B, num_expert, 1, 1, 1]
            w = topk_weights.unsqueeze(-1).unsqueeze(-1).unsqueeze(-1) # Shape: [B, num_expert, 1, 1, 1]

            # Broadcasting을 통해 가중치 적용
            # weighted_outputs shape: [B, num_expert, C, H, W]
            weighted_outputs = selected_outputs * w

            # 5. 가중치가 적용된 출력들을 합산합니다. (dim=1, num_expert 차원)
            # final_expert_contribution shape: [B, C, H, W]
            final_expert_contribution = torch.sum(weighted_outputs, dim=1)

            # 6. 원본 입력에 더합니다.
            out = inputs.clone() + final_expert_contribution
            # --- JIT 호환 버전 끝 ---
                   
        return out

    

class Expert(nn.Module):
    def __init__(self,
                 in_ch: int,
                 low_dim: int,):
        super().__init__()
        self.conv_1 = nn.Conv2d(in_ch, low_dim, kernel_size=1, padding=0)
        self.conv_2 = nn.Conv2d(in_ch, low_dim, kernel_size=1, padding=0)
        self.conv_3 = nn.Conv2d(low_dim, in_ch, kernel_size=1, padding=0)
                
    def forward(self, x: torch.Tensor, k: torch.Tensor) -> torch.Tensor:
        x = self.conv_1(x)
        x = self.conv_2(k) * x # here no more sigmoid
        x = self.conv_3(x)
        return x
    
    
class Router(nn.Module):
    def __init__(self,
                 in_ch: int,
                 num_experts: int):
        super().__init__()
        
        self.body = nn.Sequential(
            nn.AdaptiveAvgPool2d(1),
            Rearrange('b c 1 1 -> b c'),
            nn.Linear(in_ch, num_experts, bias=False),
        )
        
    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return self.body(x)
        
    
    
#################
# Utilities
#################
class StripedConv2d(nn.Module):
    def __init__(self,
                 in_ch: int,
                 kernel_size: int,
                 depthwise: bool = False):
        super().__init__()
        self.in_ch = in_ch
        self.kernel_size = kernel_size
        self.padding = kernel_size // 2
        
        self.conv = nn.Sequential(
            nn.Conv2d(in_ch, in_ch, kernel_size=(1, self.kernel_size), padding=(0, self.padding), groups=in_ch if depthwise else 1),
            nn.Conv2d(in_ch, in_ch, kernel_size=(self.kernel_size, 1), padding=(self.padding, 0), groups=in_ch if depthwise else 1),
        )
        
    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return self.conv(x)


class GatedFFN(nn.Module):
    def __init__(self, 
                 in_ch,
                 mlp_ratio,
                 kernel_size,
                 act_layer,):
        super().__init__()
        mlp_ch = in_ch * mlp_ratio
        
        self.fn_1 = nn.Sequential(
            nn.Conv2d(in_ch, mlp_ch, kernel_size=1, padding=0),
            act_layer,
        )
        self.fn_2 = nn.Sequential(
            nn.Conv2d(in_ch, in_ch, kernel_size=1, padding=0),
            act_layer,
        )
        
        self.gate = nn.Conv2d(mlp_ch // 2, mlp_ch // 2, 
                              kernel_size=kernel_size, padding=kernel_size // 2, groups=mlp_ch // 2)

    def feat_decompose(self, x):
        s = x - self.gate(x)
        x = x + self.sigma * s
        return x
    
    def forward(self, x: torch.Tensor):
        x = self.fn_1(x)
        x, gate = torch.chunk(x, 2, dim=1)
        
        gate = self.gate(gate)
        x = x * gate
        
        x = self.fn_2(x)
        return x
    
    
    
class LayerNorm(nn.Module):
    r""" LayerNorm that supports two data formats: channels_last (default) or channels_first. 
    The ordering of the dimensions in the inputs. channels_last corresponds to inputs with 
    shape (batch_size, height, width, channels) while channels_first corresponds to inputs 
    with shape (batch_size, channels, height, width).
    """
    def __init__(self, normalized_shape, eps=1e-6, data_format="channels_last"):
        super().__init__()
        self.weight = nn.Parameter(torch.ones(normalized_shape))
        self.bias = nn.Parameter(torch.zeros(normalized_shape))
        self.eps = eps
        self.data_format = data_format
        if self.data_format not in ["channels_last", "channels_first"]:
            raise NotImplementedError 
        self.normalized_shape = (normalized_shape, )
    
    def forward(self, x):
        if self.data_format == "channels_last":
            return F.layer_norm(x, self.normalized_shape, self.weight, self.bias, self.eps)
        elif self.data_format == "channels_first":
            u = x.mean(1, keepdim=True)
            s = (x - u).pow(2).mean(1, keepdim=True)
            x = (x - u) / torch.sqrt(s + self.eps)
            x = self.weight[:, None, None] * x + self.bias[:, None, None]
            return x