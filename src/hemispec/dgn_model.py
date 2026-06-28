from __future__ import annotations

from pathlib import Path


def _require_torch():
    try:
        import torch
        import torch.nn as nn
    except ImportError as exc:
        raise ImportError(
            "DGN inference requires PyTorch. Install the model extra with "
            "`python -m pip install hemispec-toolkit[model]` or install torch in this environment."
        ) from exc
    return torch, nn


class _TorchBacked:
    pass


def create_generator():
    torch, nn = _require_torch()

    class Down3d(nn.Module):
        def __init__(self, in_channels: int, out_channels: int):
            super().__init__()
            self.conv = nn.Sequential(
                nn.Conv3d(in_channels, out_channels, kernel_size=3, stride=2, padding=1),
                nn.BatchNorm3d(out_channels),
                nn.ReLU(inplace=True),
            )

        def forward(self, x):
            return self.conv(x)

    class Up3d(nn.Module):
        def __init__(self, in_channels: int, out_channels: int, stride: int, padding: int, output_padding: int):
            super().__init__()
            self.dcov = nn.Sequential(
                nn.ConvTranspose3d(
                    in_channels,
                    out_channels,
                    kernel_size=3,
                    stride=stride,
                    padding=padding,
                    output_padding=output_padding,
                ),
                nn.BatchNorm3d(out_channels),
                nn.LeakyReLU(inplace=True),
            )

        def forward(self, x):
            return self.dcov(x)

    class Generator(nn.Module):
        def __init__(self):
            super().__init__()
            self.down1 = Down3d(1, 64)
            self.down2 = Down3d(64, 64)
            self.down3 = Down3d(64, 128)
            self.down4 = Down3d(128, 256)
            self.bottle = nn.Conv3d(256, 5000, 1)
            self.up1 = Up3d(5000, 256, 2, 1, 0)
            self.up2 = Up3d(256, 128, 2, 1, 1)
            self.up3 = Up3d(128, 64, 2, 1, 1)
            self.up4 = Up3d(64, 64, 2, 1, 1)
            self.out = nn.Sequential(
                nn.Conv3d(64, 1, 2, 1, 0),
                nn.Sigmoid(),
            )

        def forward(self, inp):
            x = self.down1(inp)
            x = self.down2(x)
            x = self.down3(x)
            x = self.down4(x)
            x = self.bottle(x)
            x = self.up1(x)
            x = self.up2(x)
            x = self.up3(x)
            x = self.up4(x)
            return self.out(x)

    return Generator()


def load_generator(checkpoint: str | Path, device: str = "auto"):
    torch, _ = _require_torch()
    resolved_device = resolve_device(device)
    model = create_generator().to(resolved_device)
    try:
        payload = torch.load(str(checkpoint), map_location=resolved_device, weights_only=True)
    except TypeError:
        payload = torch.load(str(checkpoint), map_location=resolved_device)
    state_dict = payload.get("state_dict", payload) if isinstance(payload, dict) else payload
    model.load_state_dict(state_dict, strict=True)
    model.eval()
    return model


def resolve_device(device: str = "auto") -> str:
    torch, _ = _require_torch()
    if device == "auto":
        return "cuda" if torch.cuda.is_available() else "cpu"
    if device == "cuda" and not torch.cuda.is_available():
        raise RuntimeError("CUDA was requested for DGN inference, but PyTorch reports CUDA is unavailable.")
    if device not in {"cpu", "cuda"}:
        raise ValueError("device must be one of: auto, cpu, cuda")
    return device
