from transformers import LlamaConfig, AutoTokenizer, AutoModelForCausalLM
hf_token = "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"
model_name = "meta-llama/Llama-3.2-1B-Instruct"
local_dir = "./llama3_cleaned"
config = LlamaConfig.from_pretrained(model_name, token=hf_token)
config.rope_scaling = {
    "type": "linear",
    "factor": 2.0
}
config.save_pretrained(local_dir)
tokenizer = AutoTokenizer.from_pretrained(model_name, token=hf_token)
tokenizer.save_pretrained(local_dir)
model = AutoModelForCausalLM.from_pretrained(
    model_name,
    config=config,
    token=hf_token
)
model.save_pretrained(local_dir)