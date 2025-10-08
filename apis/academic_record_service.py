"""
Academic Record Service - Python translation of C# AcademicRecordRepository
"""
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field
from django.db import connections
import logging

logger = logging.getLogger(__name__)


@dataclass
class StudentTermDetails:
    """Equivalent to C# StudentTermDetails class"""
    StudentMajorDesc: str = ""
    StudentMajorCode: str = ""
    StudentStatusDesc: str = ""
    StudentStatusCode: str = ""
    TermCode: str = ""


@dataclass
class StudentCourse:
    """Equivalent to C# StudentCourse class"""
    CRSE_ID: str = ""
    CRN: str = ""
    CRSE_TITLE: str = ""
    GRADE_TITLE: str = ""
    TERM_CREDIT_HOURS: float = 0.0
    GRADE_CODE: str = ""
    Point: float = 0.0


@dataclass
class StudentGpaInfo:
    """Equivalent to C# StudentGpaInfo class"""
    SHRTGPA_HOURS_PASSED: float = 0.0
    SHRTGPA_HOURS_ATTEMPTED: float = 0.0
    SHRTGPA_HOURS_EARNED: float = 0.0
    SHRTGPA_GPA_HOURS: float = 0.0
    SHRTGPA_QUALITY_POINTS: float = 0.0
    SHRTGPA_GPA: float = 0.0
    HoursRecorded: float = 0.0


@dataclass
class StudentOverallGpa:
    """Equivalent to C# StudentOverallGpa class"""
    HoursAttempted: float = 0.0
    HoursEarned: float = 0.0
    GpaHours: float = 0.0
    QualityPoints: float = 0.0
    AverageGpa: Optional[float] = None
    HoursRecorded: float = 0.0


@dataclass
class StudentAcademicTerm:
    """Equivalent to C# StudentAcadmicTerm class"""
    StudentTermDetails: Optional["StudentTermDetails"] = None
    StudentCourses: List["StudentCourse"] = field(default_factory=list)
    StudentGpaInfo: Optional["StudentGpaInfo"] = None
    StudentOverallGpa: Optional["StudentOverallGpa"] = None


@dataclass
class StudentAcademicInfo:
    """Equivalent to C# StudentAcadmicInfo class"""
    PIDM: str = ""
    Terms: List["StudentAcademicTerm"] = field(default_factory=list)


class AcademicRecordService:
    """Python equivalent of C# AcademicRecordRepository"""
    
    def __init__(self):
        self.banner_db = connections['banner']
    
    def get_academic_record_details_sync(self, student_academic_info: StudentAcademicInfo) -> None:
        """
        Synchronous version of get_academic_record_details
        Main method to get academic record details
        """
        try:
            with self.banner_db.cursor() as cursor:
                # Get grade terms
                grade_terms = self._get_grade_terms_sync(student_academic_info, cursor)
                
                # Prepare query SQL
                sql = self._prepare_query_sql()
                
                # Process each term
                for target_term_code in grade_terms:
                    student_academic_term = StudentAcademicTerm()
                    student_academic_info.Terms.append(student_academic_term)
                    
                    # Get term details
                    self._get_term_details_sync(student_academic_info, cursor, sql, target_term_code, student_academic_term)
                    
                    # Get courses for this term
                    self._get_courses_sync(student_academic_info, cursor, target_term_code, student_academic_term)
                    
                    # Get GPA info for this term
                    self._get_gpa_info_sync(student_academic_info, cursor, target_term_code, student_academic_term)
                    
                    # Get overall GPA
                    self._get_overall_gpa_sync(student_academic_info, cursor, target_term_code, student_academic_term)
                    
        except Exception as e:
            logger.error(f"Error getting academic record details: {e}")
            raise
    
    async def get_academic_record_details(self, student_academic_info: StudentAcademicInfo) -> None:
        """
        Main method to get academic record details
        Equivalent to C# GetAcadmicRecordDetails
        """
        try:
            with self.banner_db.cursor() as cursor:
                # Get grade terms
                grade_terms = await self._get_grade_terms(student_academic_info, cursor)
                
                # Prepare query SQL
                sql = self._prepare_query_sql()
                
                # Process each term
                for target_term_code in grade_terms:
                    student_academic_term = StudentAcademicTerm()
                    student_academic_info.Terms.append(student_academic_term)
                    
                    # Get term details
                    await self._get_term_details(student_academic_info, cursor, sql, target_term_code, student_academic_term)
                    
                    # Get courses for this term
                    await self._get_courses(student_academic_info, cursor, target_term_code, student_academic_term)
                    
                    # Get GPA info for this term
                    await self._get_gpa_info(student_academic_info, cursor, target_term_code, student_academic_term)
                    
                    # Get overall GPA
                    await self._get_overall_gpa(student_academic_info, cursor, target_term_code, student_academic_term)
                    
        except Exception as e:
            logger.error(f"Error getting academic record details: {e}")
            raise
    
    def _get_grade_terms_sync(self, student_academic_info: StudentAcademicInfo, cursor) -> List[str]:
        """
        Synchronous version of get_grade_terms
        Get distinct grade terms for student
        """
        sql = """
            SELECT DISTINCT TERM_CODE 
            FROM SEU_REP.SEU_STUDENT_GRADES 
            WHERE PIDM = %s 
            ORDER BY 1 ASC
        """
        
        cursor.execute(sql, [student_academic_info.PIDM])
        rows = cursor.fetchall()
        return [row[0] for row in rows]
    
    async def _get_grade_terms(self, student_academic_info: StudentAcademicInfo, cursor) -> List[str]:
        """
        Get distinct grade terms for student
        Equivalent to C# GetGradeTermAsync
        """
        sql = """
            SELECT DISTINCT TERM_CODE 
            FROM SEU_REP.SEU_STUDENT_GRADES 
            WHERE PIDM = %s 
            ORDER BY 1 ASC
        """
        
        cursor.execute(sql, [student_academic_info.PIDM])
        rows = cursor.fetchall()
        return [row[0] for row in rows]
    
    def _prepare_query_sql(self) -> str:
        """
        Prepare the main query SQL
        Equivalent to C# PrepareQuerySql
        """
        return """
            SELECT stvmajr_desc As StudentMajorDesc, stvmajr_code As StudentMajorCode,
                   stvstst_desc As StudentStatusDesc, SGBSTDN_STST_CODE As StudentStatusCode
            FROM sgbstdn s
            LEFT JOIN stvmajr ON s.sgbstdn_majr_code_1 = stvmajr_code
            LEFT JOIN stvstst ON s.sgbstdn_stst_code = stvstst_code
            WHERE sgbstdn_term_code_eff = (
                SELECT MAX(sgbstdn_term_code_eff)
                FROM sgbstdn
                WHERE sgbstdn_pidm = s.sgbstdn_pidm AND sgbstdn_term_code_eff <= %s
            )
            AND sgbstdn_pidm = %s
        """
    
    def _get_term_details_sync(self, student_academic_info: StudentAcademicInfo, cursor, sql: str, 
                              target_term_code: str, student_academic_term: StudentAcademicTerm) -> None:
        """
        Synchronous version of get_term_details
        Get term details for a specific term
        """
        cursor.execute(sql, [target_term_code, student_academic_info.PIDM])
        row = cursor.fetchone()
        
        if row:
            student_term_details = StudentTermDetails(
                StudentMajorDesc=row[0] or "",
                StudentMajorCode=row[1] or "",
                StudentStatusDesc=row[2] or "",
                StudentStatusCode=row[3] or "",
                TermCode=target_term_code
            )
            student_academic_term.StudentTermDetails = student_term_details
    
    async def _get_term_details(self, student_academic_info: StudentAcademicInfo, cursor, sql: str, 
                               target_term_code: str, student_academic_term: StudentAcademicTerm) -> None:
        """
        Get term details for a specific term
        Equivalent to C# GetTermAsync
        """
        cursor.execute(sql, [target_term_code, student_academic_info.PIDM])
        row = cursor.fetchone()
        
        if row:
            student_term_details = StudentTermDetails(
                StudentMajorDesc=row[0] or "",
                StudentMajorCode=row[1] or "",
                StudentStatusDesc=row[2] or "",
                StudentStatusCode=row[3] or "",
                TermCode=target_term_code
            )
            student_academic_term.StudentTermDetails = student_term_details
    
    def _get_courses_sync(self, student_academic_info: StudentAcademicInfo, cursor, 
                         target_term_code: str, student_academic_term: StudentAcademicTerm) -> None:
        """
        Synchronous version of get_courses
        Get courses for a specific term
        """
        sql = """
            SELECT CRSE_ID, CRN, CRSE_TITLE, GRADE_TITLE, TERM_CREDIT_HOURS, GRADE_CODE 
            FROM SEU_STUDENT_GRADES 
            WHERE TERM_CODE = %s AND PIDM = %s
        """
        
        cursor.execute(sql, [target_term_code, student_academic_info.PIDM])
        rows = cursor.fetchall()
        
        courses = []
        for row in rows:
            course = StudentCourse(
                CRSE_ID=row[0] or "",
                CRN=row[1] or "",
                CRSE_TITLE=row[2] or "",
                GRADE_TITLE=row[3] or "",
                TERM_CREDIT_HOURS=float(row[4]) if row[4] else 0.0,
                GRADE_CODE=row[5] or ""
            )
            
            # Calculate grade points
            credit_hours_int = int(round(course.TERM_CREDIT_HOURS))
            course.Point = self._get_grade_points(course.GRADE_TITLE, credit_hours_int)
            
            courses.append(course)
        
        student_academic_term.StudentCourses = courses
    
    async def _get_courses(self, student_academic_info: StudentAcademicInfo, cursor, 
                          target_term_code: str, student_academic_term: StudentAcademicTerm) -> None:
        """
        Get courses for a specific term
        Equivalent to C# GetCoursesAsync
        """
        sql = """
            SELECT CRSE_ID, CRN, CRSE_TITLE, GRADE_TITLE, TERM_CREDIT_HOURS, GRADE_CODE 
            FROM SEU_STUDENT_GRADES 
            WHERE TERM_CODE = %s AND PIDM = %s
        """
        
        cursor.execute(sql, [target_term_code, student_academic_info.PIDM])
        rows = cursor.fetchall()
        
        courses = []
        for row in rows:
            course = StudentCourse(
                CRSE_ID=row[0] or "",
                CRN=row[1] or "",
                CRSE_TITLE=row[2] or "",
                GRADE_TITLE=row[3] or "",
                TERM_CREDIT_HOURS=float(row[4]) if row[4] else 0.0,
                GRADE_CODE=row[5] or ""
            )
            
            # Calculate grade points
            credit_hours_int = int(round(course.TERM_CREDIT_HOURS))
            course.Point = self._get_grade_points(course.GRADE_TITLE, credit_hours_int)
            
            courses.append(course)
        
        student_academic_term.StudentCourses = courses
    
    def _get_grade_points(self, grade_title: str, credit_hours: int) -> float:
        """
        Calculate grade points based on grade and credit hours
        Equivalent to C# GetGrade
        """
        grade_mapping = {
            "A+": 4.0,
            "A": 3.75,
            "B+": 3.5,
            "B": 3.0,
            "C+": 2.5,
            "C": 2.0,
            "D+": 1.5,
            "D": 1.0,
            "F": 0.0
        }
        
        grade_point = grade_mapping.get(grade_title, 0.0)
        return credit_hours * grade_point
    
    def _get_gpa_info_sync(self, student_academic_info: StudentAcademicInfo, cursor, 
                          target_term_code: str, student_academic_term: StudentAcademicTerm) -> None:
        """
        Synchronous version of get_gpa_info
        Get GPA information for a specific term
        """
        sql = """
            SELECT SHRTGPA_HOURS_PASSED, SHRTGPA_HOURS_ATTEMPTED, SHRTGPA_HOURS_EARNED,
                   SHRTGPA_GPA_HOURS, SHRTGPA_QUALITY_POINTS, SHRTGPA_GPA
            FROM shrtgpa 
            WHERE SHRTGPA_PIDM = %s AND SHRTGPA_GPA_TYPE_IND = 'I' AND SHRTGPA_TERM_CODE = %s
        """
        
        cursor.execute(sql, [student_academic_info.PIDM, target_term_code])
        row = cursor.fetchone()
        
        if row:
            gpa_info = StudentGpaInfo(
                SHRTGPA_HOURS_PASSED=float(row[0]) if row[0] else 0.0,
                SHRTGPA_HOURS_ATTEMPTED=float(row[1]) if row[1] else 0.0,
                SHRTGPA_HOURS_EARNED=float(row[2]) if row[2] else 0.0,
                SHRTGPA_GPA_HOURS=float(row[3]) if row[3] else 0.0,
                SHRTGPA_QUALITY_POINTS=float(row[4]) if row[4] else 0.0,
                SHRTGPA_GPA=float(row[5]) if row[5] else 0.0
            )
            
            # Calculate hours recorded from courses
            gpa_info.HoursRecorded = sum(course.TERM_CREDIT_HOURS for course in student_academic_term.StudentCourses)
            
            student_academic_term.StudentGpaInfo = gpa_info
    
    async def _get_gpa_info(self, student_academic_info: StudentAcademicInfo, cursor, 
                           target_term_code: str, student_academic_term: StudentAcademicTerm) -> None:
        """
        Get GPA information for a specific term
        Equivalent to C# GetgapInfoAsync
        """
        sql = """
            SELECT SHRTGPA_HOURS_PASSED, SHRTGPA_HOURS_ATTEMPTED, SHRTGPA_HOURS_EARNED,
                   SHRTGPA_GPA_HOURS, SHRTGPA_QUALITY_POINTS, SHRTGPA_GPA
            FROM shrtgpa 
            WHERE SHRTGPA_PIDM = %s AND SHRTGPA_GPA_TYPE_IND = 'I' AND SHRTGPA_TERM_CODE = %s
        """
        
        cursor.execute(sql, [student_academic_info.PIDM, target_term_code])
        row = cursor.fetchone()
        
        if row:
            gpa_info = StudentGpaInfo(
                SHRTGPA_HOURS_PASSED=float(row[0]) if row[0] else 0.0,
                SHRTGPA_HOURS_ATTEMPTED=float(row[1]) if row[1] else 0.0,
                SHRTGPA_HOURS_EARNED=float(row[2]) if row[2] else 0.0,
                SHRTGPA_GPA_HOURS=float(row[3]) if row[3] else 0.0,
                SHRTGPA_QUALITY_POINTS=float(row[4]) if row[4] else 0.0,
                SHRTGPA_GPA=float(row[5]) if row[5] else 0.0
            )
            
            # Calculate hours recorded from courses
            gpa_info.HoursRecorded = sum(course.TERM_CREDIT_HOURS for course in student_academic_term.StudentCourses)
            
            student_academic_term.StudentGpaInfo = gpa_info
    
    def _get_overall_gpa_sync(self, student_academic_info: StudentAcademicInfo, cursor, 
                             target_term_code: str, student_academic_term: StudentAcademicTerm) -> None:
        """
        Synchronous version of get_overall_gpa
        Get overall GPA information
        """
        sql = """
            SELECT 
                SUM(shrtgpa_hours_attempted) AS HoursAttempted, 
                SUM(shrtgpa_hours_earned) AS HoursEarned,
                SUM(shrtgpa_gpa_hours) AS GpaHours,
                SUM(shrtgpa_quality_points) AS QualityPoints,
                CASE 
                    WHEN SUM(shrtgpa_gpa_hours) = 0 THEN NULL 
                    ELSE ROUND(SUM(shrtgpa_quality_points) / SUM(shrtgpa_gpa_hours), 3) 
                END AS AverageGpa
            FROM shrtgpa d 
            WHERE shrtgpa_pidm = %s 
              AND shrtgpa_gpa_type_ind = 'I' 
              AND shrtgpa_term_code IN (
                  SELECT DISTINCT TERM_CODE 
                  FROM SEU_REP.SEU_STUDENT_GRADES 
                  WHERE PIDM = d.shrtgpa_pidm AND TERM_CODE <= %s
              )
        """
        
        cursor.execute(sql, [student_academic_info.PIDM, target_term_code])
        row = cursor.fetchone()
        
        if row:
            overall_gpa = StudentOverallGpa(
                HoursAttempted=float(row[0]) if row[0] else 0.0,
                HoursEarned=float(row[1]) if row[1] else 0.0,
                GpaHours=float(row[2]) if row[2] else 0.0,
                QualityPoints=float(row[3]) if row[3] else 0.0,
                AverageGpa=float(row[4]) if row[4] else None
            )
            
            # Calculate hours recorded from all terms
            all_courses = []
            for term in student_academic_info.Terms:
                all_courses.extend(term.StudentCourses)
            
            overall_gpa.HoursRecorded = sum(course.TERM_CREDIT_HOURS for course in all_courses)
            
            student_academic_term.StudentOverallGpa = overall_gpa
    
    async def _get_overall_gpa(self, student_academic_info: StudentAcademicInfo, cursor, 
                              target_term_code: str, student_academic_term: StudentAcademicTerm) -> None:
        """
        Get overall GPA information
        Equivalent to C# GetOverallGpaAsync
        """
        sql = """
            SELECT 
                SUM(shrtgpa_hours_attempted) AS HoursAttempted, 
                SUM(shrtgpa_hours_earned) AS HoursEarned,
                SUM(shrtgpa_gpa_hours) AS GpaHours,
                SUM(shrtgpa_quality_points) AS QualityPoints,
                CASE 
                    WHEN SUM(shrtgpa_gpa_hours) = 0 THEN NULL 
                    ELSE ROUND(SUM(shrtgpa_quality_points) / SUM(shrtgpa_gpa_hours), 3) 
                END AS AverageGpa
            FROM shrtgpa d 
            WHERE shrtgpa_pidm = %s 
              AND shrtgpa_gpa_type_ind = 'I' 
              AND shrtgpa_term_code IN (
                  SELECT DISTINCT TERM_CODE 
                  FROM SEU_REP.SEU_STUDENT_GRADES 
                  WHERE PIDM = d.shrtgpa_pidm AND TERM_CODE <= %s
              )
        """
        
        cursor.execute(sql, [student_academic_info.PIDM, target_term_code])
        row = cursor.fetchone()
        
        if row:
            overall_gpa = StudentOverallGpa(
                HoursAttempted=float(row[0]) if row[0] else 0.0,
                HoursEarned=float(row[1]) if row[1] else 0.0,
                GpaHours=float(row[2]) if row[2] else 0.0,
                QualityPoints=float(row[3]) if row[3] else 0.0,
                AverageGpa=float(row[4]) if row[4] else None
            )
            
            # Calculate hours recorded from all terms
            all_courses = []
            for term in student_academic_info.Terms:
                all_courses.extend(term.StudentCourses)
            
            overall_gpa.HoursRecorded = sum(course.TERM_CREDIT_HOURS for course in all_courses)
            
            student_academic_term.StudentOverallGpa = overall_gpa


def convert_academic_info_to_dict(academic_info: StudentAcademicInfo) -> Dict[str, Any]:
    """
    Convert StudentAcademicInfo to dictionary for JSON serialization
    """
    return {
        "PIDM": academic_info.PIDM,
        "Terms": [
            {
                "StudentTermDetails": {
                    "StudentMajorDesc": term.StudentTermDetails.StudentMajorDesc if term.StudentTermDetails else "",
                    "StudentMajorCode": term.StudentTermDetails.StudentMajorCode if term.StudentTermDetails else "",
                    "StudentStatusDesc": term.StudentTermDetails.StudentStatusDesc if term.StudentTermDetails else "",
                    "StudentStatusCode": term.StudentTermDetails.StudentStatusCode if term.StudentTermDetails else "",
                    "TermCode": term.StudentTermDetails.TermCode if term.StudentTermDetails else ""
                },
                "StudentCourses": [
                    {
                        "CRSE_ID": course.CRSE_ID,
                        "CRN": course.CRN,
                        "CRSE_TITLE": course.CRSE_TITLE,
                        "GRADE_TITLE": course.GRADE_TITLE,
                        "TERM_CREDIT_HOURS": course.TERM_CREDIT_HOURS,
                        "GRADE_CODE": course.GRADE_CODE,
                        "Point": course.Point
                    } for course in term.StudentCourses
                ],
                "StudentGpaInfo": {
                    "SHRTGPA_HOURS_PASSED": term.StudentGpaInfo.SHRTGPA_HOURS_PASSED if term.StudentGpaInfo else 0.0,
                    "SHRTGPA_HOURS_ATTEMPTED": term.StudentGpaInfo.SHRTGPA_HOURS_ATTEMPTED if term.StudentGpaInfo else 0.0,
                    "SHRTGPA_HOURS_EARNED": term.StudentGpaInfo.SHRTGPA_HOURS_EARNED if term.StudentGpaInfo else 0.0,
                    "SHRTGPA_GPA_HOURS": term.StudentGpaInfo.SHRTGPA_GPA_HOURS if term.StudentGpaInfo else 0.0,
                    "SHRTGPA_QUALITY_POINTS": term.StudentGpaInfo.SHRTGPA_QUALITY_POINTS if term.StudentGpaInfo else 0.0,
                    "SHRTGPA_GPA": term.StudentGpaInfo.SHRTGPA_GPA if term.StudentGpaInfo else 0.0,
                    "HoursRecorded": term.StudentGpaInfo.HoursRecorded if term.StudentGpaInfo else 0.0
                },
                "StudentOverallGpa": {
                    "HoursAttempted": term.StudentOverallGpa.HoursAttempted if term.StudentOverallGpa else 0.0,
                    "HoursEarned": term.StudentOverallGpa.HoursEarned if term.StudentOverallGpa else 0.0,
                    "GpaHours": term.StudentOverallGpa.GpaHours if term.StudentOverallGpa else 0.0,
                    "QualityPoints": term.StudentOverallGpa.QualityPoints if term.StudentOverallGpa else 0.0,
                    "AverageGpa": term.StudentOverallGpa.AverageGpa if term.StudentOverallGpa else None,
                    "HoursRecorded": term.StudentOverallGpa.HoursRecorded if term.StudentOverallGpa else 0.0
                }
            } for term in academic_info.Terms
        ]
    } 