import os

def generate_sample_data():
    resumes_dir = "data/resumes"
    jds_dir = "data/jds"
    os.makedirs(resumes_dir, exist_ok=True)
    os.makedirs(jds_dir, exist_ok=True)

    jds = {
        "jd_1.txt": "Looking for a Python developer with SQL and Machine Learning experience. Docker and Kubernetes are a plus.",
        "jd_2.txt": "Frontend engineer needed. Must know React, JavaScript, HTML, CSS. TypeScript is nice to have.",
        "jd_3.txt": "Data Scientist required. Skills: Python, R, Data Analysis, Machine Learning, Deep Learning, PyTorch."
    }

    resumes = {
        "res_1.txt": "Alice Smith\nalice@example.com\n555-123-4567\nB.S. Computer Science\nSkills: Python, SQL, Machine Learning, Data Analysis, Docker. Experience building scalable pipelines.",
        "res_2.txt": "Bob Johnson\nbob@example.com\nSkills: Java, Spring Boot, MySQL. Worked on enterprise backends.",
        "res_3.txt": "Charlie Brown\ncharlie@email.com\nFrontend dev: React, JavaScript, HTML, CSS, TypeScript. 5 years experience.",
        "res_4.txt": "Diana Prince\ndiana.prince@mail.com\nData Scientist. B.A. Math. Skills: Python, Deep Learning, PyTorch, TensorFlow, Machine Learning.",
        "res_5.txt": "Eve Adams\neve@example.com\nFull stack: Python, Django, React, JavaScript, SQL.",
        "res_6.txt": "Frank Castle\nfrank@email.com\nDevOps engineer. Docker, Kubernetes, AWS, Jenkins, Linux.",
        "res_7.txt": "Grace Hopper\ngrace@example.com\nPioneer in CS. Skills: Java, C++, Python, SQL.",
        "res_8.txt": "Hank Pym\nhank@example.com\nSkills: C++, Rust, Go. Systems programming.",
        "res_9.txt": "Ivy Pepper\nivy@email.com\nSkills: R, Data Analysis, Python, Machine Learning.",
        "res_10.txt": "Jack Ryan\njack@example.com\nAnalyst. SQL, Excel, Data Analysis, Python.",
        "res_11.txt": "Karen Page\nkaren@example.com\nJournalist turning coder. Python, HTML, CSS.",
        "res_12.txt": "Leo Fitz\nleo@email.com\nEngineer. Python, Machine Learning, Docker, SQL, Kubernetes.",
        "res_13.txt": "Mia Toretto\nmia@example.com\nUI/UX Designer. Figma, Adobe, HTML, CSS.",
        "res_14.txt": "Nick Fury\nnick@email.com\nManager. Agile, Scrum, Project Management.",
        "res_15.txt": "Olivia Pope\nolivia@example.com\nFixer. Java, C#, SQL, Azure.",
        "res_16.txt": "Peter Parker\npeter@example.com\nWeb Dev. React, Node.js, JavaScript, MongoDB.",
        "res_17.txt": "Quinn Fabray\nquinn@email.com\nMobile Dev. Swift, iOS, Java, Android.",
        "res_18.txt": "Rachel Green\nrachel@example.com\nFashion Data. Python, Data Analysis, SQL.",
        "res_19.txt": "Steve Rogers\nsteve@email.com\nOld school. C, Assembly, Linux.",
        "res_20.txt": "Tony Stark\ntony@example.com\nGenius. Python, C++, Machine Learning, Deep Learning, PyTorch, React, Docker, Kubernetes."
    }

    for name, content in jds.items():
        with open(os.path.join(jds_dir, name), "w") as f:
            f.write(content)

    for name, content in resumes.items():
        with open(os.path.join(resumes_dir, name), "w") as f:
            f.write(content)

    # Labeled pairs (Resume, JD) -> Label (Good, OK, Poor)
    labels = [
        ("res_1.txt", "jd_1.txt", "Good"),
        ("res_2.txt", "jd_1.txt", "Poor"),
        ("res_3.txt", "jd_2.txt", "Good"),
        ("res_4.txt", "jd_3.txt", "Good"),
        ("res_5.txt", "jd_1.txt", "OK"),
        ("res_6.txt", "jd_1.txt", "OK"), # has docker, k8s
        ("res_7.txt", "jd_1.txt", "OK"), # python, sql
        ("res_8.txt", "jd_2.txt", "Poor"),
        ("res_9.txt", "jd_3.txt", "Good"),
        ("res_10.txt", "jd_1.txt", "OK"),
        ("res_11.txt", "jd_2.txt", "Poor"),
        ("res_12.txt", "jd_1.txt", "Good"),
        ("res_13.txt", "jd_2.txt", "OK"),
        ("res_14.txt", "jd_1.txt", "Poor"),
        ("res_15.txt", "jd_1.txt", "Poor"),
        ("res_16.txt", "jd_2.txt", "Good"),
        ("res_17.txt", "jd_3.txt", "Poor"),
        ("res_18.txt", "jd_3.txt", "OK"),
        ("res_19.txt", "jd_1.txt", "Poor"),
        ("res_20.txt", "jd_3.txt", "Good")
    ]
    
    with open("eval/labels.csv", "w") as f:
        f.write("Resume,JD,True_Label\n")
        for r, j, l in labels:
            f.write(f"{r},{j},{l}\n")

if __name__ == "__main__":
    generate_sample_data()
