import io


def alphabetize_words_in_text_file(input_file_path, output_file_path):
  """Alphabetizes words in a text file that has one word per line.

  Args:
    input_file_path: The path to the input text file.
    output_file_path: The path to the output text file.
  """

  with io.open(input_file_path, "r", encoding="utf-8") as input_file:
    words = input_file.readlines()

  # Strip whitespace from the words.
  words = [word.strip() for word in words]

  # Sort the words alphabetically.
  words.sort()

  with io.open(output_file_path, "w", encoding="utf-8") as output_file:
    for word in words:
      output_file.write(word + "\n")


if __name__ == "__main__":
  input_file_path = input("Path and file name: ")
  output_file_path = "output.txt"

  # Alphabetize the words in the input text file and write them to the output text file.
  alphabetize_words_in_text_file(input_file_path, output_file_path)
