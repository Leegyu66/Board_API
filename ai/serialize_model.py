import torch

from core.SeemoRe import SeemoRe_T
from core.MambaIRv2_L import MambaIRv2_L

model = MambaIRv2_L()
model.load_state_dict(torch.load("./weights/MambaIRv2_L.pt"), strict=True)
model.cuda()

scripted_model = torch.jit.script(model)
torch.jit.save(scripted_model, "./weights/model.pt")
# model = SeemoRe_T()
# model.load_state_dict(torch.load("./weights/SeemoRe_T.pth")['params'], strict=True)
# model.cuda()

# scripted_model = torch.jit.script(model)
# torch.jit.save(scripted_model, "./weights/model.pt")