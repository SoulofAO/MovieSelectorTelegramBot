from openai import OpenAI
from typing import List, Callable

client = OpenAI(
  api_key="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"
)

chat_gpt_context = '''
Ты являешься частью кода циклического ИИ программирования на Python. 
Сначала описывается первичная задача и прописываются тесты. 
Тесты делятся на три типа - прогон работоспособности (для упрощения - назовем его компиляцией), сгенерированные и пользовательские. при необходимости. 
Затем действие отдается в цикл к Chat GPT, и ты занимаешься тем, что генерируешь код. Далее код отправляет его на проверку.
Проверка прогоняет тесты и в случае успешности всех тестов возвращает True. Иначе ошибка и неправильный код предыдущей модели возвращается обратно в цикл. 
Между циклами помимо кода в качестве контекста сохраняется изначальная задача программы, количество итераций и прочие пояснения.
 
 Исходя из этого - 1. Возвращай текст с пометками START CODE и END CODE указывающими что из этого является кодом. 
 Код представлен в виде обычного текста. 
 В случае неизвестного тебе API имеешь право на гуглинг информации. 
 Прочие действия можешь давать в виде стандартизированных комментариев. 
'''
class GPTClient:
    def __init__(self):
        pass
    def generate_code(self, task_description: str, context: str) -> str:
        """Generates code based on the task description and context."""
        completion = client.chat.completions.create(
            model="gpt-4",
            store=True,
            messages=[
                {"role": "system", "content": chat_gpt_context},
                {"role": "user", "content": f"Task: {task_description}\nContext: {context}"},
            ],
            max_tokens = 1000,
        )
        return completion.choices[0].message.content

def extract_code(input_text):
    start_marker = "START CODE"
    end_marker = "END CODE"

    start_index = input_text.find(start_marker)
    end_index = input_text.find(end_marker)

    if start_index == -1 or end_index == -1 or start_index > end_index:
        return ""  # Если метки не найдены или расположены некорректно

    # Смещаем индексы, чтобы исключить метки
    start_index += len(start_marker)
    return input_text[start_index:end_index].strip()


# Test runner
class TestRunner:
    @staticmethod
    def run_tests(code: str, tests: List[Callable]) -> bool:
        """Runs a series of tests on the generated code."""
        try:
            exec_locals = {}
            exec(extract_code(code), {}, exec_locals)  # Execute code in isolated context

            for test in tests:
                if not test(exec_locals):
                    return False
            return True
        except Exception as e:
            print(f"Execution error: {e}")
            return False

# Cyclic AI Programming Loop
def cyclic_programming(task_description: str, tests: List[Callable], max_iterations: int = 1):
    client = GPTClient()
    context = ""  # Stores accumulated context between iterations
    last_code = ""

    for iteration in range(1, max_iterations + 1):
        print(f"\nIteration {iteration}:")
        generated_code = client.generate_code(task_description, context)
        print(f"Generated code:\n{generated_code}\n")

        # Run tests
        generated_code.replace("START CODE", "")
        if TestRunner.run_tests(generated_code, tests):
            print("All tests passed!")
            return generated_code
        else:
            print("Tests failed. Adding feedback to context.")
            context += f"\nIteration {iteration} feedback: Code failed tests.\nCode:\n{generated_code}\n"
            last_code = generated_code

    print("\nMax iterations reached. Returning the last generated code.")
    return last_code

# Example usage
def main():
    task_description = "Write a function `add(a, b)` that returns the sum of two numbers."

    # Define tests
    def test_add_1(locals):
        return locals['add'](2, 3) == 5

    def test_add_2(locals):
        return locals['add'](-1, 1) == 0

    def test_add_3(locals):
        return locals['add'](0, 0) == 0

    tests = [test_add_1, test_add_2, test_add_3]

    # Run cyclic programming loop
    final_code = cyclic_programming(task_description, tests)
    print(f"\nFinal code:\n{final_code}")

if __name__ == "__main__":
    main()
