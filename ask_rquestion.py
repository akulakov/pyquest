#!/usr/bin/env python

import os, sys, shelve, random
from pprint import pprint

show_right_ans = False     # print right answer if user got it wrong

qfname = "questions.db"
questions = []


def load_questions():
    qfp = shelve.open(qfname)
    for key in qfp.keys():
        for question in qfp[key]:
            questions.append((key, question))


def ask_text(question):
    """ Ask a question, return true or false.

        Question looks like: (question, ((answer,0), (answer,1),) ...) where 1
        means the right answer.
        Return question text and the number of the right answer & text string of
        right answer.
    """
    random.shuffle(question[1])
    ans = question[1]
    text = ""
    text += question[0][1] + "\n"
    for a in range(len(ans)):
        text += "%d) %s\n" % (a+1,ans[a][0])
        if ans[a][1] == 1:
            right_num = a+1
            right_answer = ans[a][0]
    text += "> \n"
    return (text, right_num, right_answer)


def ask(question):
    """ Ask a question, return true or false.

        Question looks like: (question, ((answer,0), (answer,1),) ...) where 1
        means the right answer.

        Returns is_right, right_ans # where is_right is 0 or 1, and right_ans is a
        string.

    """
    random.shuffle(question[1])
    ans = question[1]
    while True:
        print (question[0][1])
        right_ans = None
        for a in range(len(ans)):
            print ("%d) %s" % (a+1,ans[a][0]))
            if ans[a][1]:
                right_ans = ans[a][0]
        answer = raw_input("=====> ")
        if answer == "q":
            sys.exit()
        try:
            answer = int(answer)
        except:
            continue
        if answer > len(ans) or answer < 1:
            continue
        return ans[answer-1][1], right_ans


def test_ask_text():
    q = ["In low-level light conditions, the eyes of Tawny Owl are:",
        [["50 times better than human eyes.", 0],
        ["100 times better than human eyes.", 1],
        ["200 times better than human eyes.", 0],
        ["300 times better than human eyes.", 0],]]
    tmp = ask_text(q)
    assert tmp[2] == "100 times better than human eyes."

    print ("Tests passed!")


def tests():
    test_ask_text()


def main():
    load_questions()
    pprint(questions[0])
    tests()

    q = random.choice(questions)[1]
    text, right_num, right_ans = ask_text(q)
    print (text)
    print ("Right answer:", right_ans)
    print ("\n\n")

    while True:
        q = random.choice(questions)[1]
        result, right_ans = ask(q)
        if result:
            print("!!!Right answer!!!!")
            print()
        else:
            print("...Wrong answer...",)
            if show_right_ans:
                print("(%s)" % right_ans)
            else:
                print()
            print()

if __name__ == "__main__":
    main()
