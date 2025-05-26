import pickle


def train_model(user_logs):
    # Placeholder: use scikit-learn or other library to train
    pass


def predict_action(user_input, model):
    return model.predict([user_input])[0]


def save_model(model, filepath):
    with open(filepath, 'wb') as f:
        pickle.dump(model, f)


def load_model(filepath):
    try:
        with open(filepath, 'rb') as f:
            return pickle.load(f)
    except FileNotFoundError:
        return DummyModel()


class DummyModel:
    def predict(self, X):
        return ["play" for _ in X]