import torch

from core.SeemoRe import SeemoRe_T

model = SeemoRe_T()
model.load_state_dict(torch.load("./weights/SeemoRe_T.pth")['params'], strict=True)
model.cuda()

scripted_model = torch.jit.script(model)
torch.jit.save(scripted_model, "./weights/model.pt")