"""
Script to use simpletransformers to fine-tune BERT for Named Entity Recognition (NER) task.
"""
import os
from io import StringIO
import pandas as pd
from sklearn.metrics import accuracy_score
from sklearn.preprocessing import LabelEncoder
from sklearn.model_selection import train_test_split
from simpletransformers.ner import NERModel, NERArgs
from other.red import input_red


def load_data(
        csv_file: StringIO = None, display_data: bool = False
) -> pd.core.frame.DataFrame:
    """
    This function loads the dataset and preprocesses it to be used by the transformer.
    @param csv_file: dataset containing tagged sentences
    @param display_data: boolean to print the amount of columns in csv_file
    @rtype: pandas DataFrame
    @return: formatted dataset which is parsable by transformer
    """
    if csv_file is None:
        data_path = os.path.join(os.path.dirname(os.path.realpath(__file__)), "../..",
                                 "other/datasets", "ner_dataset.csv")
        data = pd.read_csv(data_path)
    elif isinstance(csv_file, StringIO):
        data = pd.read_csv(csv_file)
    else:
        raise SystemExit(f"Must either use default csv file path or pass in a csv file,"
                         f" got {type(csv_file)}.")

    data["sentence_number"] = LabelEncoder().fit_transform(data["sentence_number"])

    data.rename(columns={"sentence_number": "sentence_id", "word": "words", "tag": "labels"},
                inplace=True)
    data["labels"] = data["labels"].str.upper()

    if display_data:
        print(data.head(len(data)))

    return data


def __labels__(
        data: pd.core.frame.DataFrame
) -> []:
    """
    This function returns the unique labels in the dataset.
    @param data: formatted dataset
    @rtype: list(str)
    @return: list of labels ex. B-COFFEE-TYPE, I-BAKERY-ITEM
    """
    return data["labels"].unique().tolist()


def __args__(

) -> NERArgs:
    """
    This function returns the arguments for the NER class.
    @rtype: NERArgs
    @return: class which contains args/params for NER class
    """
    args = NERArgs()
    args.num_train_epochs = 12
    args.learning_rate = 1e-4
    args.overwrite_output_dir = True
    args.train_batch_size = 32
    args.eval_batch_size = 32

    return args


def separate_into_test_and_train(
        data: pd.core.frame.DataFrame
) -> tuple and tuple:
    """
    This function splits the dataset into training and testing data (80% training, 20% testing).
    @param data: formatted dataset
    @rtype: 2x tuple[DataFrame, DataFrame]
    @return: dataset split into train (80% original) and test (20% original)
    """
    x = data[["sentence_id", "words"]]
    y = data["labels"]

    # 80% training, 20% test
    x_train, x_test, y_train, y_test = train_test_split(x, y, test_size=0.2)

    train_data = pd.DataFrame(
        {
            "sentence_id": x_train["sentence_id"],
            "words": x_train["words"],
            "labels": y_train
        }
    )
    test_data = pd.DataFrame(
        {
            "sentence_id": x_test["sentence_id"],
            "words": x_test["words"],
            "labels": y_test
        }
    )

    return train_data, test_data


def fine_tune_ner_bert(
        model_save_path: str = None
) -> bool:
    """
    This function fine-tunes BERT for NER task.
    @param model_save_path: if you want to change default save path of `other/genai_models/`
    @rtype: bool
    @return: boolean to know training was success
    """
    if input_red("ARE YOU SURE YOU WANT TO DELETE AND REFINE BERT: ") != "YES":
        return False

    if str(input("Enter the passkey to confirm: ")) != "beanKnowsWhatBeanWants":
        return False

    save_path = os.path.join(os.path.dirname(os.path.realpath(__file__)), "../..",
                             "other/genai_models/ner_model")
    data = load_data()

    if data.empty:
        return False

    train, test = separate_into_test_and_train(data)

    if train.empty or test.empty:
        return False


    model = NERModel('bert',
                     'bert-base-cased',
                     labels=__labels__(data),
                     args=__args__(),
                     use_cuda=False)

    model.train_model(train, eval_data=test, acc=accuracy_score)

    if model_save_path:
        model.save_model(model_save_path, model=model.model)
    else:
        model.save_model(save_path, model=model.model)

    result, _, _ = model.eval_model(test)

    print(result)

    return True


def main(

) -> int:  # pragma: no cover
    """
    @rtype: int
    @return: 0 if successful
    """
    fine_tune_ner_bert()

    return 0


if __name__ == "__main__":  # pragma: no cover
    main()
