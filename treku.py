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


BASE_URL = "https://na.trekuniversity.com"

LOGIN_URL = BASE_URL + "/login/authorize"

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

# resp = urllib.request.urlopen(urllib.request.Request(COURSES_URL))

bs = BeautifulSoup(resp.read(), "html.parser")

school_list = bs.find_all(class_="schools-wrap")[0]
schools = [
    {"title": e.text, "url": e["href"]}
    for e in school_list.find_all("a")
    if e["href"] != "#" and not e.has_attr("title")
]

print(schools)

courses = []
for school in schools:
    print(school)
    resp = urllib.request.urlopen(urllib.request.Request(BASE_URL + school["url"]))
    # req = urllib.request.urlopen(urllib.request.Request('http://na.gt.cyclingprophet.com' + school['url']))
    # resp = urllib.request.urlopen(req)
    # print(resp.read())
    bs = BeautifulSoup(resp.read(), "html.parser")

    uhg = bs.find(class_="module-pool").find_all(attrs={"class": "module-item-wrap"})
    for e in uhg:
        if "Completed" not in str(e):
            c = e.find("a")
            if c["href"] != "#" and c.has_attr("title"):
                courses.append({
                    "title": c["title"],
                    "url": c["href"],
                    "passed": True if "DONE" in c.text else False,
                })
 

unfinished = list(filter(lambda x: not x["passed"], courses))

print(courses)


for un in unfinished:
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
                results = bs.find_all("table")[0].find_all("tr")
                for q, r, i in zip(
                    sorted(course.questions, key=lambda x: x.current_iter_question_num),
                    results,
                    range(20),
                ):
                    correct = r.find("i", class_="fa-times") == None
                    q.get_answer().is_correct = "correct" if correct else "incorrect"
                    crct = "correct" if correct else "incorrect"
                    #print("question: {} answer was {} {}\n{}\n".format(i+1,crct,q.get_answer().text,q.text))
                    #print(q)
                    #print(*q.answers,sep="\n")
                    #print("CORRECT" if correct else "INCORRECT")
                    #print("q: {} ans: {}, {}".format(q.number, q.get_answer().id, "CORRECT" if correct else "INCORRECT"))
                #print("all done")
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

                question = course.get_question_by_number(question_id)
                if not question:
                    question = Question(text, question_id)
                    question.answers = [
                        Answer(e.find("input")["value"], e.find("label").text)
                        for e in bs.find("ol").find_all("li")
                    ]
                    course.questions += [question]
                questionNum = int(bs.find("input", id="question_counter")["value"])
                question.current_iter_question_num = questionNum

                #print(text)
                answer = question.get_answer()

                ans = {
                    "answer": answer.id,
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
                            "answer": answer.id,
                            "question_id": question_id,
                            "question_counter": questionNum,
                            "question_retake": "",
                            "submit_type": "submit",
                        }
                    ).encode("UTF-8"),
                )

                #print("question: {}\n entering {} {}".format(question.text,answer.is_correct,answer.text))
