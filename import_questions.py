"""import questions - process questions text files and create a shelve or
pickle file with a database of questions.

questions are taken from all txt files in questions dir.

To use, simply run import_questions.py"""

import os, sys, shelve, glob

dbfile = "questions.db"

test_text = """
10
In low-level light conditions, the eyes of Tawny Owl are:
50 times better than human eyes.
100 times better than human eyes.<<
200 times better than human eyes.
300 times better than human eyes.
--
5
Tawny owl usually nests in:
Holes in trees.<<
Holes in ridges.
Nests on branches.
Decrepit human structures.
--
6
Tawny owl is a:
Small-sized owl.
Medium-sized owl.<<
Large-sized owl.
The smallest owl.
--
9
Tawny owl has a wingspan of:
55-62cm.
62-72cm.
81-96cm.<<
96-105cm.
"""


def process(text):
    text = text.replace("\r", "")
    qlist = []
    foo = text.split("--\n")
    import pprint
    # pprint.pprint(foo)
    foo = [a for a in foo if a.strip()]
    for bar in foo:
        baz = bar.split("\n")
        baz = [a for a in baz if a.strip()]
        difficulty = baz[0]
        question = baz[1]
        answers = baz[2:]
        alst = []
        no_right = True
        for a in answers:
            if a.endswith("<<"):  # right answer
                alst.append((a.rstrip('<'),1))
                no_right = False
            else:
                alst.append((a,0))
        if no_right:
            print ("No right answer! Question: %s Exiting.."  % question)
            sys.exit()
        qlist.append(((difficulty, question),alst))

    return qlist

def test_process():
    qlist = process(test_text)
    # print "len of qlist", len(qlist)
    # print "qlist", qlist
    assert len(qlist) == 4

    for (d, q), answers in qlist:
        if q == "In low-level light conditions, the eyes of Tawny Owl are:":
            assert ("50 times better than human eyes.", 0) in answers
            assert ("100 times better than human eyes.", 1) in answers
            assert ("200 times better than human eyes.", 0) in answers
            assert ("300 times better than human eyes.", 0) in answers
        elif q == "Tawny owl usually nests in:":
            assert ("Holes in ridges.", 0) in answers
            assert ("Holes in trees.", 1) in answers
            assert ("Nests on branches.", 0) in answers
            assert ("Decrepit human structures.", 0) in answers
        elif q == "Tawny owl is a:":
            assert ("Small-sized owl.", 0) in answers
            assert ("Medium-sized owl.", 1) in answers
            assert ("Large-sized owl.", 0) in answers
            assert ("The smallest owl.", 0) in answers
        elif q == "Tawny owl has a wingspan of:":
            assert ("55-62cm.", 0) in answers
            assert ("62-72cm.", 0) in answers
            assert ("81-96cm.", 1) in answers
            assert ("96-105cm.", 0) in answers
        else:
            raise "ERROR: invalid entry in qdict in test_process!"

    print ("Tests passed!")

def tests():
    test_process()


def main():
    tests()

    files = glob.glob("questions/*.txt")
    dbfp = shelve.open(dbfile)
    for file in files:
        print("file:", file)
        # fp = open(os.path.join("questions", file))
        fp = open(file)
        name = fp.readline()[:-1]   # strip newline
        fp.readline()               # name divider
        text = fp.read()
        # print "Text: "
        # print text
        qlist = process(text)
        print("%d questions added" % len(qlist))

        # import pprint
        # pprint.pprint(qlist)

        dbfp[name] = qlist

    dbfp.close()


main()
