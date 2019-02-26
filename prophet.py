#!/usr/bin/env python3

from bs4 import BeautifulSoup
import urllib, http.cookiejar, re

# this will only run on python 3
# this is some ugly, hastily-written code
# ...
# sorry

# set these to your prophet user and pass

USERNAME = 'yourusername'
PASSWORD = 'yourpass'


BASE_URL = "https://na.cannondale.cyclingprophet.com"

LOGIN_URL = BASE_URL + "/login/authorize"

if USERNAME == '' or PASSWORD == '':
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

                
class Question:
        def __init__(self, text, number):
                self.text = text
                self.number = number
                self.answers = []


        def get_answer_by_text(self, text):
                return list(filter(lambda x: x.text == text, self.answers))[0]

        # gets correct answer if known otherwise unknown answer
        def get_answer(self):
                return sorted(filter(lambda x: x.is_correct in ["correct","unknown"], self.answers), key=lambda x: x.is_correct)[0] 
        
        def is_correct(self):
                return len(answers) > 0 and self.get_answer() == "correct"

class Answer:
	def __init__(self, id, text):
		self.id = id
		self.text = text
		self.is_correct = "unknown"

jar = http.cookiejar.CookieJar()


# schools can be find in <a>s in ul#school-dropdown

urllib.request.install_opener(urllib.request.build_opener(urllib.request.HTTPCookieProcessor(jar)))


req = urllib.request.Request(LOGIN_URL, urllib.parse.urlencode({'user_name': USERNAME, 'password': PASSWORD, 'rem': 'false' }).encode('UTF-8'))
resp = urllib.request.urlopen(req)

#print(resp.read())

#resp = urllib.request.urlopen(urllib.request.Request(COURSES_URL))

bs = BeautifulSoup(resp.read(), "html.parser")

school_list = bs.find(id="school-dropdown")
schools = [{'title': e.text, 'url': e['href']} for e in school_list.find_all('a') if e['href'] != "#"]
courses = []
for school in schools:
	resp = urllib.request.urlopen(urllib.request.Request(BASE_URL + school['url']))
	#req = urllib.request.urlopen(urllib.request.Request('http://na.gt.cyclingprophet.com' + school['url']))
	#resp = urllib.request.urlopen(req)
	bs = BeautifulSoup(resp.read(), "html.parser")
	b = [{'title': c['title'], 'url': c['href'], 'passed': True if "DONE" in c.text else False} for c in bs.find(class_="schools-list").find_all("a") if c['href'] != '#']
	
	courses.extend(b)





unfinished = list(filter(lambda x: not x['passed'], courses))

print(courses)


for un in unfinished:
        print(un['title'] + "\n\t"+un['url']+"\n")

        coursenum = re.sub("\D", "", un['url'])

        course = Course(un['title'],coursenum,un['url']+"start/")
        #unfinishedcourses += [course]

        # start quiz and run through all questions
        while not course.passed:
                nextreq = urllib.request.Request(BASE_URL+un['url']+"/retake")              
                ajaxurl = BASE_URL+"/module/ajaxquiz/"+course.coursenum
                while True:
                        resp = urllib.request.urlopen(nextreq)
                        p = resp.read()
                        if "Quiz Results" in str(p) or "Congratu" in str(p):
                                bs = BeautifulSoup(p, "html.parser")
                                course.passed = "Sorry" not in str(p) or "Congratu" in str(p)
                                if course.passed:
                                        print("\n#########################\n\tPASSED!\n#########################\n")
                                        break
                                results = bs.find_all("table")[0].find_all('tr')
                                for q,r in zip(course.questions, results):
                                        correct = r.find('img', alt="x") == None
                                        q.get_answer().is_correct = "correct" if correct else "incorrect"
                                        print("question: "+q.text+"\n answer was "+"correct" if correct else "incorrect")
                                        
                                        
                                
                                print("all done")
                                break
                        bs = BeautifulSoup(p, "html.parser")

                        question = bs.find('input', id="question_id")

                        if not question:
                                print("video question")
                                ans = {'no_quiz_video_watched': 'true', 'first_time_quiz_credits': 50}
                                nextreq = urllib.request.Request(ajaxurl, urllib.parse.urlencode(ans).encode('UTF-8'))
                        else:
                                question_id = question['value']
                                text = bs.find('p', class_="question").get_text()

                                question = course.get_question_by_number(question_id)
                                if not question:
                                        question = Question(text, question_id)
                                        question.answers = [Answer(e.find('input')['value'], e.find('label').text) for e in bs.find('ol').find_all('li')]
                                        course.questions += [question]
                                answer = question.get_answer()



                                ans = {'answer': answer.id, 'question': question_id, 'question_retake': "retake", 'submit_type': "submit"}
                                nextreq = urllib.request.Request(ajaxurl, urllib.parse.urlencode({'answer': answer.id, 'question_id': question_id, 'question_retake': "retake", 'submit_type': "submit"}).encode('UTF-8'))

                                print("question: "+question.text+"\n entering "+answer.is_correct+" "+answer.text)

        
        

