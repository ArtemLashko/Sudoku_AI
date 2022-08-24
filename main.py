from Parser import Parser
from Board import Board


if __name__ == "__main__":
    b = Parser("Tests/1.jpeg").get_result()
    a = Board(b, True).get_res()
