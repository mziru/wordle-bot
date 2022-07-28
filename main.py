import time

from selenium import webdriver
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.action_chains import ActionChains

from webdriver_manager.chrome import ChromeDriverManager

from functools import lru_cache

def parse_data_states(round: int) ->  list[tuple[int, str]]:
    """
    Parses html on wordle site to return feedback for each letter of the last word guessed.
    :param round: int, between 1 and 6
    :return: list of feedback tuples (integer, string).
        (0, 'absent') -- letter is not in the solution word
        (1, 'present;) -- letter is in the solution word but in a different position
        (2, 'correct') -- letter is in the solution and in the correct position
    """
    state_dict = {'absent': 0, 'present': 1, 'correct': 2}
    state_list = []
    for i in range(1, 6):
        element = driver.find_element(
            By.XPATH,
            '//*[@id="wordle-app-game"]/div[1]/div/div[{}]/div[{}]/div'.format(round, i))
        state_str = element.get_attribute('data-state')
        state_int = state_dict[state_str]

        state_list.append((state_int, state_str))

    return state_list

@lru_cache(maxsize=None)
def calc_response_vector(w1, w2):
    tw2 = w2
    msum = [0 for i in range(5)]
    for c_ind in range(5):
        if w1[c_ind] == tw2[c_ind]:
            msum[c_ind] = 2
            tw2 = tw2[:c_ind] + "*" + tw2[c_ind + 1:]
    for c_ind in range(5):
        if w1[c_ind] in tw2 and msum[c_ind] == 0:
            msum[c_ind] = 1
            ind_app = tw2.find(w1[c_ind])
            tw2 = tw2[:ind_app] + "*" + tw2[ind_app + 1:]
    return msum

driver = webdriver.Chrome(service=ChromeService(ChromeDriverManager().install()))
actions = ActionChains(driver)

driver.get("https://www.nytimes.com/games/wordle/")

element = driver.find_element(By.CLASS_NAME, "Modal-module_closeIcon__b4z74")
element.click()

f = open("wordle-answers-alphabetical.txt", "r")
all_w = open("words.txt", "r")

lines = f.readlines()
all_lines = all_w.readlines()

for round in range(6):
    min_wc = 100000
    chosen_word = ""
    srmat = {}
    if round != 0:
        all_it = all_lines
        # all_it = all_lines
    else:
        all_it = ["aesir"]

    for w1 in all_it:
        w1 = w1.strip()
        mat = {}
        rmat = {}
        for w2 in lines:
            w2 = w2.strip()
            msum = calc_response_vector(w1, w2)
            if tuple(msum) not in rmat:
                rmat[tuple(msum)] = [w2]
            else:
                rmat[tuple(msum)].append(w2)
            mat[w1, w2] = msum

        M = max([len(val) for val in rmat.values()])
        if M < min_wc:
            min_wc = M
            chosen_word = w1
            srmat = rmat

    actions.send_keys(chosen_word + Keys.ENTER)
    actions.perform()
    print('round:', round + 1)
    print(len(lines), 'possible words remain')
    if len(lines) <= 15:
        print('possible words:', lines)
    print('guess:', chosen_word.upper())

    time.sleep(2)

    states = parse_data_states(round + 1)
    print('feedback parse:', [state[1] for state in states])
    print('thinking...')
    print()

    feedback = tuple([int(el[0]) for el in states])
    lines = srmat[feedback]
    if len(lines) == 1:
        actions.send_keys(lines[0] + Keys.ENTER)
        actions.perform()
        print('round:', round + 2)
        print("Done! The answer is {}".format(lines[0].upper()))
        exit(0)

print("Failed. Did not find word after 6 attempts")
