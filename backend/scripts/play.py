from backend.game.session import Game
from backend.llm.provider import OllamaProvider
from backend.validation.case_validator import confirm_case

DEBUG = True  # show when the guard blocks a reply; turn off for a demo


def main():
    case = confirm_case("case01")
    game = Game(case, OllamaProvider(), debug=DEBUG)

    print(f"COLD CASE: {case.title}")
    for item in case.public_info:
        print(f"- {item}")
    print("Type /help for commands.\n")

    while True:
        line = input("> ").strip()
        if line.lower() in ("/quit", "quit"):
            break
        for out in game.handle(line):
            print(out)
        if game.finished:
            break


if __name__ == "__main__":
    main()
