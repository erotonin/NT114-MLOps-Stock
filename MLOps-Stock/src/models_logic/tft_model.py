import torch
import torch.nn as nn
import torch.nn.functional as F

class GatedResidualNetwork(nn.Module):
    def __init__(self, input_size, hidden_size, output_size, dropout=0.1):
        super(GatedResidualNetwork, self).__init__()
        self.lin1 = nn.Linear(input_size, hidden_size)
        self.lin2 = nn.Linear(hidden_size, output_size) # Should be output_size
        self.gate = nn.Linear(hidden_size, output_size) # Should be output_size
        self.skip = nn.Linear(input_size, output_size) if input_size != output_size else nn.Identity()
        self.dropout = nn.Dropout(dropout)
        self.norm = nn.LayerNorm(output_size)

    def forward(self, x):
        encoded = F.elu(self.lin1(x))
        h = self.lin2(encoded)
        g = torch.sigmoid(self.gate(encoded))
        # Gating Mechanism (GLU-like)
        h = g * h 
        # Residual connection
        return self.norm(self.skip(x) + self.dropout(h))

class VariableSelectionNetwork(nn.Module):
    def __init__(self, input_size, num_vars, hidden_size, dropout=0.1):
        super(VariableSelectionNetwork, self).__init__()
        self.grns = nn.ModuleList([GatedResidualNetwork(input_size, hidden_size, hidden_size, dropout) for _ in range(num_vars)])
        self.selector_grn = GatedResidualNetwork(num_vars * input_size, hidden_size, num_vars, dropout)
        self.softmax = nn.Softmax(dim=-1)

    def forward(self, x):
        # x: [batch, num_vars, input_size]
        var_outputs = []
        for i, grn in enumerate(self.grns):
            var_outputs.append(grn(x[:, i]))
        
        var_outputs = torch.stack(var_outputs, dim=1) # [batch, num_vars, hidden_size]
        
        # Selection weights
        flattened_x = x.view(x.size(0), -1)
        weights = self.softmax(self.selector_grn(flattened_x)).unsqueeze(2) # [batch, num_vars, 1]
        
        return (weights * var_outputs).sum(dim=1) # [batch, hidden_size]

class TFTSkeleton(nn.Module):
    """
    Simplified Temporal Fusion Transformer Architecture.
    """
    def __init__(self, num_features=8, num_symbols=30, d_model=64, nhead=4, num_layers=2):
        super(TFTSkeleton, self).__init__()
        self.d_model = d_model
        
        # 1. Embeddings
        self.symbol_emb = nn.Embedding(num_symbols, d_model)
        
        # 2. Variable Selection Network (VSN)
        self.vsn = VariableSelectionNetwork(input_size=1, num_vars=num_features, hidden_size=d_model)
        
        # 3. Temporal Processing (LSTM + Attention)
        self.lstm = nn.LSTM(d_model, d_model, batch_first=True)
        
        decoder_layer = nn.TransformerEncoderLayer(
            d_model=d_model, nhead=nhead, dim_feedforward=d_model*4, batch_first=True
        )
        self.transformer = nn.TransformerEncoder(decoder_layer, num_layers=num_layers)
        
        # 4. Output Head
        self.output_head = nn.Linear(d_model, 1) # Single value T+3 prediction

    def forward(self, x, symbol_idx=0):
        # x: [batch, seq_len, num_features]
        batch, seq, feat = x.shape
        
        # Input processing via True VSN
        # Reshape for VSN: [batch * seq, num_features, 1 (input_size)]
        x_reshaped = x.view(batch * seq, feat, 1)
        x_vsn = self.vsn(x_reshaped) # Output: [batch * seq, d_model]
        x = x_vsn.view(batch, seq, self.d_model) # Back to sequence: [batch, seq, d_model]
        
        # Symbol embedding integration
        if not isinstance(symbol_idx, torch.Tensor):
            symbol_idx = torch.tensor([symbol_idx], device=x.device)
        sym = self.symbol_emb(symbol_idx).view(-1, 1, self.d_model).expand(batch, seq, -1)
        
        x = x + sym
        
        # Temporal features (LSTM)
        x_lstm, _ = self.lstm(x)
        
        # Global Attention (Transformer)
        x_attn = self.transformer(x_lstm)
        
        # Last token for T+3 prediction
        out = x_attn[:, -1, :]
        return self.output_head(out)

if __name__ == "__main__":
    # Test
    model = TFTSkeleton()
    x = torch.randn(2, 60, 8)
    out = model(x)
    print(f"Output shape: {out.shape}") # [2, 1]
