from enum import Enum

class MlModel(Enum):
    Gpt = "gpt4o-mini"
    Mistral = "mistral"

if __name__ == "__main__":
    model = MlModel.Gpt
    print(model.value)
