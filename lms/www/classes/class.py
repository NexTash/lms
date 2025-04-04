import frappe
from lms.lms.utils import has_course_moderator_role
from frappe import _
from frappe.utils import getdate
from lms.www.utils import get_assessments


def get_context(context):
	context.no_cache = 1
	class_name = frappe.form_dict["classname"]
	session_user = []
	remaining_students = []
	context.is_moderator = has_course_moderator_role()

	context.class_info = frappe.db.get_value(
		"LMS Class",
		class_name,
		[
			"name",
			"title",
			"start_date",
			"end_date",
			"description",
			"custom_component",
			"seat_count",
			"start_time",
			"end_time",
		],
		as_dict=True,
	)

	context.published_courses = frappe.get_all(
		"LMS Course", {"published": 1}, ["name", "title"]
	)

	context.class_courses = frappe.get_all(
		"Class Course",
		{"parent": class_name},
		["name", "course", "title"],
		order_by="creation desc",
	)

	class_students = frappe.get_all(
		"Class Student",
		{"parent": class_name},
		["student", "student_name", "username"],
		order_by="creation desc",
	)

	for student in class_students:
		if student.student == frappe.session.user:
			session_user.append(student)
		else:
			remaining_students.append(student)

	if len(session_user):
		context.class_students = session_user + remaining_students
	else:
		context.class_students = class_students

	students = [student.student for student in class_students]
	context.is_student = frappe.session.user in students

	context.live_classes = frappe.get_all(
		"LMS Live Class",
		{"class_name": class_name, "date": [">=", getdate()]},
		["title", "description", "time", "date", "start_url", "join_url", "owner"],
		order_by="date",
	)

	context.assessments = get_assessments(class_name)
	context.all_assignments = get_all_assignments(class_name)
	context.all_quizzes = get_all_quizzes(class_name)


def get_all_quizzes(class_name):
	all_quizzes = frappe.get_all(
		"LMS Quiz", {"owner": frappe.session.user}, ["name", "title"]
	)
	for quiz in all_quizzes:
		quiz.checked = frappe.db.exists(
			{
				"doctype": "LMS Assessment",
				"assessment_type": "LMS Quiz",
				"assessment_name": quiz.name,
				"parent": class_name,
			}
		)
	return all_quizzes


def get_all_assignments(class_name):
	all_assignments = frappe.get_all(
		"LMS Assignment", {"owner": frappe.session.user}, ["name", "title"]
	)
	for assignment in all_assignments:
		assignment.checked = frappe.db.exists(
			{
				"doctype": "LMS Assessment",
				"assessment_type": "LMS Assignment",
				"assessment_name": assignment.name,
				"parent": class_name,
			}
		)
	return all_assignments
