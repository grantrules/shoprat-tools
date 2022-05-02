#!/usr/bin/env python3

from bs4 import BeautifulSoup
import urllib, http.cookiejar, re, time
from random import choice

# this will only run on python 3
# this is some ugly, hastily-written code
# ...
# sorry

# set these to your prophet user and pass

USERNAME = ""
PASSWORD = ""


BASE_URL = "https://na.s-tec.shimano.com"

LOGIN_URL = BASE_URL + "/login/authorize"
COURSES_URL = BASE_URL + "/courses/all"

if USERNAME == "" or PASSWORD == "":
    print("Hey doofus, edit this file first and put your login info")
    quit()


class Course:
    def __init__(self, title, coursenum, url):
        self.title = title
        self.coursenum = coursenum
        self.url = url
        self.passed = False
        self.questions = []

    def get_question_by_number(self, number):
        x = list(filter(lambda x: x.number == number, self.questions))
        return x[0] if len(x) > 0 else None

    def __str__(self):
        return "{} {} {} {} {}".format(self.title,self.coursenum,self.url,self.passed,self.questions)


class Question:
    def __init__(self, text, number):
        self.text = text.strip()
        self.number = number
        self.answers = []

    def get_answer_by_text(self, text):
        return list(filter(lambda x: x.text == text, self.answers))[0]

    # gets correct answer if known otherwise unknown answer
    def get_answer(self):
        ans = sorted(
            filter(lambda x: x.is_correct in ["correct", "unknown"], self.answers),
            key=lambda x: x.is_correct,
        )
        if len(ans) == 0:
            #print("problem with {}".format(self.text))
            #print(*self.answers)
            return self.answers[0]
            #return choice(self.answers)
        return ans[0]

    def is_correct(self):
        return len(self.answers) > 0 and self.get_answer() == "correct"
    
    def __str__(self):
        return "{} {}".format(self.text, self.number)


class Answer:
    def __init__(self, id, text):
        self.id = id
        self.text = text.strip()
        self.is_correct = "unknown"
    def __str__(self):
        return "{} {} {}".format(self.id, self.text, self.is_correct)


jar = http.cookiejar.CookieJar()


# schools can be find in <a>s in ul#school-dropdown

urllib.request.install_opener(
    urllib.request.build_opener(urllib.request.HTTPCookieProcessor(jar))
)


req = urllib.request.Request(
    LOGIN_URL,
    urllib.parse.urlencode(
        {"user_name": USERNAME, "password": PASSWORD, "rem": "false"}
    ).encode("UTF-8"),
)
resp = urllib.request.urlopen(req)

# print(resp.read())

resp = urllib.request.urlopen(urllib.request.Request(COURSES_URL))

bs = BeautifulSoup(resp.read(), "html.parser")

courses = []
uhg = bs.find_all(class_="incomplete")
for e in uhg:

    c = e.find("a")
    courses.append({
        "title": c.text,
        "url": c["href"],
        "passed": False,
    })
 

print(courses)


for un in courses:
    print(un["title"] + "\n\t" + un["url"] + "\n")

    coursenum = re.sub("\D", "", un["url"])

    course = Course(un["title"], coursenum, un["url"] + "start/")
    # unfinishedcourses += [course]
    count = 0

    # start quiz and run through all questions
    while not course.passed:
        count = count + 1
        ajaxurl = BASE_URL + "/module/ajaxquiz/" + course.coursenum
        nextreq = ajaxurl
        for q in course.questions:
            q.current_iter_question_num = 99999
        while True:
            resp = urllib.request.urlopen(nextreq)
            p = resp.read()
            # print(p)
            if "Quiz Results" in str(p) or "Congratu" in str(p):
                bs = BeautifulSoup(p, "html.parser")
                course.passed = "Sorry" not in str(p) or "Congratu" in str(p)
                if course.passed:
                    print(
                        "\n##############################\n\tPASSED! {} tries \n##############################\n".format(count)
                    )
                    break
                print("all done")
                break
            bs = BeautifulSoup(p, "html.parser")

            question = bs.find("input", id="question_id")

            if not question:
                #print("video question")
                #print(p)

                ans = {"no_quiz_video_watched": "true", "first_time_quiz_credits": 50}
                nextreq = urllib.request.Request(
                    ajaxurl, urllib.parse.urlencode(ans).encode("UTF-8")
                )
            else:
                question_id = question["value"]
                text = bs.find("p", class_="question").get_text()

                question = Question(text, question_id)

                questionNum = int(bs.find("input", id="question_counter")["value"])
                answer_id = re.match(r".*?correctAnswer = (\d+)", bs.find('script').text.replace("\n","")).group(1)
                ans = {
                    "answer": answer_id,
                    "question": question_id,
                    "question_retake": "retake",
                    "question_counter": questionNum,
                    "submit_type": "submit",
                }
                #print(ans)
                nextreq = urllib.request.Request(
                    ajaxurl,
                    urllib.parse.urlencode(
                        {
                            "answer": answer_id,
                            "question_id": question_id,
                            "question_counter": questionNum,
                            "question_retake": "",
                            "submit_type": "submit",
                        }
                    ).encode("UTF-8"),
                )

                #print("question: {}\n entering {} {}".format(question.text,answer.is_correct,answer.text))
