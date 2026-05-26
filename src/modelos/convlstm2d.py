import torch
import torch.nn as nn
import torch.nn.functional as F


class ConvLSTMCell(nn.Module):
    'Celda ConvLSTM 2D individual.'
    def __init__(self, input_dim, hidden_dim, kernel_size=3, bias=True):
        super().__init__()
        self.hidden_dim = hidden_dim
        padding = kernel_size // 2
        self.conv = nn.Conv2d(input_dim + hidden_dim, 4 * hidden_dim,
                               kernel_size, padding=padding, bias=bias)

    def forward(self, x, prev_state):
        h_prev, c_prev = prev_state
        combined = torch.cat([x, h_prev], dim=1)
        gates = self.conv(combined)
        i, f, o, g = torch.split(gates, self.hidden_dim, dim=1)
        i = torch.sigmoid(i)
        f = torch.sigmoid(f)
        o = torch.sigmoid(o)
        g = torch.tanh(g)
        c = f * c_prev + i * g
        h = o * torch.tanh(c)
        return h, c


class ConvLSTM2D(nn.Module):
    'ConvLSTM 2D + Positional Encoding + cabezas separadas por contaminante.'

    def __init__(self, input_channels=522, pos_channels=25, hidden_dim=64,
                 kernel_size=3, num_layers=2, num_horizons=3, num_pollutants=3,
                 dropout_prob=0.4):
        super().__init__()
        self.hidden_dim = hidden_dim
        self.num_layers = num_layers
        self.num_horizons = num_horizons
        self.num_pollutants = num_pollutants
        self.pos_encoding = nn.Parameter(torch.randn(1, 1, pos_channels, 5, 5) * 0.1)
        total_input = input_channels + pos_channels
        self.cells = nn.ModuleList()
        for _ in range(num_layers):
            self.cells.append(ConvLSTMCell(total_input, hidden_dim, kernel_size))
            total_input = hidden_dim
        self.dropout = nn.Dropout2d(dropout_prob)
        # Cabezas separadas: una Conv2d por contaminante
        # Cada cabeza predice los 3 horizontes para un contaminante
        self.output_heads = nn.ModuleList([
            nn.Conv2d(hidden_dim, num_horizons, 1) for _ in range(num_pollutants)
        ])
        self._init_weights()

    def _init_weights(self):
        for name, param in self.named_parameters():
            if "conv" in name and "weight" in name:
                nn.init.xavier_uniform_(param)
            elif "bias" in name:
                nn.init.zeros_(param)

    def forward(self, x):
        'Forward pass con positional encoding, ConvLSTM y cabezas separadas.'
        N, T, C, H, W = x.shape
        pe = self.pos_encoding.expand(N, -1, -1, -1, -1).expand(-1, T, -1, -1, -1)
        x_pe = torch.cat([x, pe], dim=2)
        h = [torch.zeros(N, self.hidden_dim, H, W, device=x.device) for _ in range(self.num_layers)]
        c = [torch.zeros(N, self.hidden_dim, H, W, device=x.device) for _ in range(self.num_layers)]
        for t in range(T):
            inp = x_pe[:, t]
            for layer in range(self.num_layers):
                h[layer], c[layer] = self.cells[layer](inp, (h[layer], c[layer]))
                inp = h[layer]
        h_last = self.dropout(h[-1])
        # Cada cabeza: (N, 3, 5, 5) -> avg pool -> (N, 3)
        outs = [head(h_last).mean(dim=[-1, -2]) for head in self.output_heads]
        # Stack en ultima dimension: (N, num_horizons, num_pollutants)
        return torch.stack(outs, dim=-1)  # (N, 3, 3): (batch, horizonte, contaminante)


def masked_mse_loss(y_pred, y_true, weights=None):
    'MSE loss que ignora valores NaN en y_true.'
    if weights is None:
        weights = torch.tensor([1.0, 1.0, 1.0], device=y_pred.device)
    weights = weights.to(y_pred.device)
    mask = ~torch.isnan(y_true)
    loss_p = torch.zeros(3, device=y_pred.device)
    for p in range(3):
        pmask = mask[:, :, p]
        if pmask.sum() > 0:
            loss_p[p] = F.mse_loss(y_pred[:, :, p][pmask], y_true[:, :, p][pmask], reduction="mean")
    return (loss_p * weights).sum() / weights.sum()
