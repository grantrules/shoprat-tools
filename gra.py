from bs4 import BeautifulSoup
import urllib, http.cookiejar, re

# this will only run on python 3
# this is some ugly, hastily-written code
# ...
# sorry

# set these to your GRA user and pass

GRA_USERNAME = ''
GRA_PASSWORD = ''

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

LOGIN_URL = "https://www.giantretailacademy.com/en-us/login/"
COURSES_URL = "https://www.giantretailacademy.com/en-us/courses/"
urllib.request.install_opener(urllib.request.build_opener(urllib.request.HTTPCookieProcessor(jar)))


req = urllib.request.Request(LOGIN_URL, urllib.parse.urlencode({'UserName': GRA_USERNAME, 'UserPassword': GRA_PASSWORD }).encode('UTF-8'))
resp = urllib.request.urlopen(req)

resp = urllib.request.urlopen(urllib.request.Request(COURSES_URL))

bs = BeautifulSoup(resp.read(), "html.parser")

b = bs.find_all("div", class_="item-course")
courses = [{
        'title': e.find('h3').get_text(),
        'url': "https://www.giantretailacademy.com"+ e.find('a',class_="button-blue")['href'] if  "Take quiz" in e.text else None,
        'passed': "Take quiz" not in e.text
        } for e in b]

unfinished = list(filter(lambda x: not x['passed'], courses))

#unfinishedcourses = []


for un in unfinished:
        print(un['title'] + "\n\t"+un['url']+"\n")

        coursenum = re.sub("\D", "", un['url'])

        course = Course(un['title'],coursenum,un['url']+"start/")
        #unfinishedcourses += [course]

        # start quiz and run through all questions
        while not course.passed:
                nextreq = urllib.request.Request(un['url'] +"start/", urllib.parse.urlencode({'course-'+coursenum:"Start the quiz"}).encode('UTF-8'))              
                while True:
                        resp = urllib.request.urlopen(nextreq)
                        if "complete" in resp.geturl():
                                bs = BeautifulSoup(resp.read(), "html.parser")
                                course.passed = len(bs.find_all('div', class_="failed")) == 0
                                if course.passed:
                                        print("\n#########################\n\tPASSED!\n#########################\n")
                                        break
                                results = bs.find_all('div', class_="item-result")
                                for q,r in zip(course.questions, results):
                                        #<td style="color:Red">Answer that was wrong</td>
                                        a = r.find_all('td')[-1]
                                        ans = a.text
                                        #print(a)
                                        #not sure why but it looks like the last answer
                                        #does not have a style attribute when the course
                                        #is passed. seems fine if it doesn't pass, though
                                        correct = "correct" if 'style' in a.attrs and "Red" not in a['style'] else "incorrect"
                                        q.get_answer_by_text(ans).is_correct = correct
                                        print("question: "+q.text+"\n answer was "+correct+" "+ans)
                                        
                                        
                                
                                print("all done")
                                break
                        bs = BeautifulSoup(resp.read(), "html.parser")
                        c = bs.find(id="course").find('div')
                        qnum = c.find('strong').text

                        text = bs.find('p', class_="question-text").text
                        question = course.get_question_by_number(qnum)
                        if not question:
                                question = Question(text, qnum)
                                question.answers = [Answer(e.find('input')['value'], e.find('label').text) for e in c.find('div').find_all('div')]
                                course.questions += [question]
                        answer = question.get_answer()

                        nextreq = urllib.request.Request(resp.geturl(), urllib.parse.urlencode({'answer': answer.id}).encode('UTF-8'))

                        print("question: "+question.text+"\n entering "+answer.is_correct+" "+answer.text)

        
        
