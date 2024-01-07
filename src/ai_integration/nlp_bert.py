from simpletransformers.ner import NERModel
from os import path
from word2number import w2n


def ner_transformer(input_string: str = None, print_prediction: bool = False) -> list:
    """

    @rtype: list of dictionaries
    @param input_string: customer request ex. "I want a black coffee"
    @param print_prediction: boolean flag to print predictions
    @return: predictions generated from fine-tuned transformer
    """
    if not input_string or not isinstance(input_string, str):
        return []

    transformer_file_path = path.join(path.dirname(path.realpath(__file__)), "../..", "other/genai_models/")

    model = NERModel('bert', transformer_file_path, use_cuda=False)

    prediction, _ = model.predict([input_string])

    if print_prediction:
        print(prediction)

    return prediction


def format_ner(ner_prediction: list, print_final_format: bool = False) -> []:
    """

    @update: Will be deleted soon
    """
    order = []
    formatted_order = []

    # removes any Outliers
    for prediction in ner_prediction:
        for entity_dict in prediction:
            for word, tag in entity_dict.items():
                if tag != 'O':
                    order.append(entity_dict)

    # turns all B_QUANTITIES into I_QUANTITIES
    temp = None
    for pair in order:
        for word, tag in pair.items():
            if tag == 'B_QUANTITY':
                temp = word
            elif tag != 'B_QUANTITY' and temp is not None:
                formatted_order.append(pair)
                formatted_order.append({temp: 'I_QUANTITY'})
                temp = None
            else:
                formatted_order.append(pair)

    intermittent_format = []
    for pair in formatted_order:
        for word, tag in pair.items():
            intermittent_format.append([word, tag])

    formatted_order = []
    prev_index = None
    for i in range(len(intermittent_format)):
        if intermittent_format[i][1] != 'I_QUANTITY':
            formatted_order.append([intermittent_format[i][0], -1])
            if i == len(intermittent_format) - 1:
                formatted_order[-1][1] = 1
            else:
                prev_index = i
        elif intermittent_format[i][1] == 'I_QUANTITY' and isinstance(intermittent_format[i][0], str):
            formatted_order[prev_index][1] = w2n.word_to_num(intermittent_format[i][0])

    if print_final_format:
        print(formatted_order)
    return formatted_order


if __name__ == "__main__":
    res = ner_transformer("Can I get a caramel latte and an egg and cheese sandwich?")
    print(res)

