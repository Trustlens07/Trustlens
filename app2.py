import streamlit as st
from PyPDF2 import PdfReader
import docx
import re
import pytesseract
from pdf2image import convert_from_bytes
from skill_analyzer import SkillAnalyzer

# ---------------- CONFIG ----------------
pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"
POPPLER_PATH = r"C:\Users\Preethi shubha\Downloads\Release-25.12.0-0\poppler-25.12.0\Library\bin"

st.set_page_config(page_title="Talent Intelligence Platform", layout="wide")
st.title("🤖 AI-Powered Talent Intelligence Platform")

skill_analyzer = SkillAnalyzer()

# ---------------- ROLE LIST ----------------
roles_list = [
    "Data Scientist","Data Analyst","Data Engineer","DevOps Engineer",
    "Backend Developer","Frontend Developer","Full Stack Developer",
    "Software Engineer","Machine Learning Engineer","AI Engineer",
    "Cloud Engineer","Cybersecurity Analyst","Mobile App Developer",
    "Game Developer","Embedded Systems Engineer","Blockchain Developer",
    "QA Engineer","Site Reliability Engineer","Software Developer",

    "Business Analyst","Product Analyst","Operations Analyst",
    "Financial Analyst","Marketing Analyst","Sales Analyst",
    "Strategy Consultant","Management Consultant",

    "Product Manager","Project Manager","Program Manager",
    "Operations Manager","HR Manager","Business Development Manager",

    "UI Designer","UX Designer","Product Designer",
    "Graphic Designer","Motion Designer",

    "Research Scientist","Research Assistant",
    "AI Researcher","Data Researcher",

    "Digital Marketing Specialist","SEO Specialist",
    "Content Strategist","Sales Executive",
    "Growth Hacker","Brand Manager",

    "Mechanical Engineer","Civil Engineer","Electrical Engineer",

    "Law Associate","Doctor","Teacher",
    "Content Writer","Journalist"
]

role_synonyms = {
    "data scientist": ["data science", "ml engineer", "ai scientist"],
    "data analyst": ["business analyst", "data analysis"],
    "data engineer": ["etl engineer", "big data engineer"],
    "software engineer": ["software developer", "sde"],
    "backend developer": ["backend engineer", "server-side developer"],
    "frontend developer": ["frontend engineer", "ui developer"],
    "full stack developer": ["fullstack developer"],
    "machine learning engineer": ["ml engineer"],
    "ai engineer": ["ai developer"],
    "devops engineer": ["devops", "site reliability engineer"],
    "cloud engineer": ["cloud developer", "cloud architect"],
    "cybersecurity analyst": ["security analyst", "infosec analyst"],
    "mobile app developer": ["android developer", "ios developer"],
    "qa engineer": ["test engineer", "software tester"],
    "product manager": ["pm"],
    "project manager": ["project lead"],
    "program manager": ["program lead"],
    "business analyst": ["ba"],
    "marketing analyst": ["marketing executive"],
    "ui designer": ["ui/ux designer"],
    "ux designer": ["user experience designer"],
    "product designer": ["ui ux designer"],
    "graphic designer": ["visual designer"],
    "motion designer": ["animation designer"],
    "research scientist": ["researcher"],
    "ai researcher": ["ml researcher"],
    "digital marketing specialist": ["digital marketer"],
    "seo specialist": ["seo expert"],
    "content writer": ["copywriter"],
    "journalist": ["reporter"],
    "mechanical engineer": ["mechanical design engineer"],
    "civil engineer": ["site engineer"],
    "electrical engineer": ["electronics engineer"],
    "doctor": ["physician"],
    "teacher": ["educator"],
    "law associate": ["legal associate"]
}

# ---------------- COMPANY SETUP ----------------
st.header("🏢 Organization Configuration")

# ---------------- ROLE INPUT ----------------
st.subheader("🎯 Position Specification")

if "role_input" not in st.session_state:
    st.session_state.role_input = ""

if "selected_role" not in st.session_state:
    st.session_state.selected_role = None

role_input = st.text_input(
    "Designated Position (Single Role Only)",
    key="role_input"
)

role = None

invalid = [",", "/", "|", "&", " and "]

if role_input:
    if any(i in role_input.lower() for i in invalid):
        st.error("❌ Please specify only one role")
    elif len(role_input.strip()) < 2:
        st.warning("⚠️ Please enter a valid position")
    else:
        suggestions = [
            r for r in roles_list 
            if role_input.lower() in r.lower()
        ][:5]
        if suggestions:
            st.markdown("**💡 Recommended Positions**")
            cols = st.columns(len(suggestions))
            for i, s in enumerate(suggestions):
                if cols[i].button(s):
                    st.session_state.selected_role = s
                    st.rerun()

if st.session_state.selected_role:
    role = st.session_state.selected_role
    st.success(f"✅ Position Confirmed: {role}")       

# ---------------- REQUIRED SKILLS ----------------
required_skills_input = st.text_area("Core Competencies Required (comma-separated)")

# ---------------- PREFERENCES ----------------
st.subheader("⚙️ Evaluation Criteria")

st.markdown("### 📊 Core Competencies")
st.write("✔ Skills Match (mandatory evaluation factor)")

use_experience = st.checkbox("Professional Experience")
use_education = st.checkbox("Educational Background")
use_certifications = st.checkbox("Professional Certifications")
use_projects = st.checkbox("Project Portfolio")
use_github = st.checkbox("Code Repository Activity")
use_internships = st.checkbox("Internship Experience")
use_domain = st.checkbox("Domain Expertise")
use_tools = st.checkbox("Technical Tool Proficiency")
use_problem_solving = st.checkbox("Analytical & Problem-Solving Capabilities")

st.markdown("### 🚀 Advanced Indicators")
use_open_source = st.checkbox("Open Source Contributions")
use_hackathons = st.checkbox("Hackathon Participation")
use_research = st.checkbox("Research Publications")
use_publications = st.checkbox("Academic Papers")

st.markdown("### 🤝 Behavioral Attributes")
use_communication = st.checkbox("Communication Proficiency")
use_leadership = st.checkbox("Leadership Experience")
use_freelance = st.checkbox("Freelance Engagements")
use_startup = st.checkbox("Startup Environment Experience")
use_gap = st.checkbox("Career Transition Flexibility")
use_multidomain = st.checkbox("Cross-Functional Experience")
use_remote = st.checkbox("Remote Work Adaptability")
use_team = st.checkbox("Collaborative Work Experience")

# ---------------- FAIRNESS ----------------
st.subheader("⚖️ Bias Mitigation Configuration")

mode = st.radio("Fairness Protocol", ["Strict", "Balanced", "Custom"])

ignore_gender = True
ignore_age = True
ignore_college = True
ignore_company = True
ignore_location = True
ignore_name = True
ignore_gap_year = False
ignore_graduation_year = False
ignore_language = False

if mode == "Strict":
    ignore_gap_year = True
    ignore_graduation_year = True
    ignore_language = True
elif mode == "Balanced":
    pass
elif mode == "Custom":
    st.markdown("### Customize Bias Mitigation")
    ignore_gender = st.checkbox("Demographic Information", value=True)
    ignore_age = st.checkbox("Age-Related Data", value=True)
    ignore_college = st.checkbox("Educational Institution", value=True)
    ignore_company = st.checkbox("Previous Employer", value=True)
    ignore_location = st.checkbox("Geographic Location", value=True)
    ignore_name = st.checkbox("Personal Identifiers", value=True)
    ignore_gap_year = st.checkbox("Career Interruption", value=False)
    ignore_graduation_year = st.checkbox("Graduation Timeline", value=False)
    ignore_language = st.checkbox("Language Proficiency", value=False)

# ---------------- RESUME UPLOAD ----------------
st.header("📄 Candidate Document Upload")
file = st.file_uploader("Upload Candidate Resume", type=["pdf", "docx"])

# ---------------- TEXT EXTRACTION FUNCTIONS ----------------
def read_docx(file):
    doc = docx.Document(file)
    return " ".join([p.text for p in doc.paragraphs])

def read_pdf(file):
    reader = PdfReader(file)
    text = ""
    for page in reader.pages:
        text += page.extract_text() or ""
    if len(text.strip()) < 100:
        file.seek(0)
        images = convert_from_bytes(file.read(), poppler_path=POPPLER_PATH)
        text = ""
        for img in images:
            text += pytesseract.image_to_string(img)
    return text

def extract_skills_from_resume(text):
    """Extract technical skills from resume"""
    text_lower = text.lower()
    
    # Common technical skills to look for
    skill_patterns = {
        "programming_languages": ["python", "java", "javascript", "c++", "c#", "ruby", "go", "rust", "swift", "kotlin", "php", "typescript", "scala"],
        "frameworks": ["react", "angular", "vue", "django", "flask", "spring", "node.js", "express", "rails", "laravel", "asp.net"],
        "databases": ["sql", "mysql", "postgresql", "mongodb", "oracle", "redis", "cassandra", "dynamodb"],
        "cloud": ["aws", "azure", "gcp", "google cloud", "cloud computing", "ec2", "s3", "lambda", "kubernetes", "docker"],
        "data_science": ["machine learning", "deep learning", "nlp", "tensorflow", "pytorch", "scikit-learn", "pandas", "numpy", "tableau", "power bi"],
        "devops": ["jenkins", "gitlab", "github actions", "ci/cd", "terraform", "ansible", "prometheus", "grafana"]
    }
    
    found_skills = []
    for category, skills in skill_patterns.items():
        for skill in skills:
            # Use word boundaries for exact matching
            pattern = r'\b' + re.escape(skill) + r'\b'
            if re.search(pattern, text_lower):
                found_skills.append(skill)
    
    return list(set(found_skills))

def analyze_resume_completeness(text):
    """Analyze resume completeness"""
    sections = {
        "contact_info": bool(re.search(r'\b\d{10}\b', text) and '@' in text),
        "summary": bool(re.search(r'\b(summary|profile|about me)\b', text.lower())),
        "experience": bool(re.search(r'\b(experience|work history|employment)\b', text.lower())),
        "education": bool(re.search(r'\b(education|degree|university|college)\b', text.lower())),
        "skills": bool(re.search(r'\b(skills|technologies|competencies)\b', text.lower())),
        "projects": bool(re.search(r'\b(projects|portfolio)\b', text.lower()))
    }
    
    completeness_score = sum(sections.values()) / len(sections) * 100
    return completeness_score, sections

def calculate_experience_years(text):
    """Estimate years of experience"""
    text_lower = text.lower()
    
    # Look for experience patterns
    patterns = [
        r'(\d+)\+?\s*years?\s+of\s+experience',
        r'experience\s+of\s+(\d+)\+?\s*years?',
        r'(\d+)\+?\s*yrs?\s+experience'
    ]
    
    for pattern in patterns:
        match = re.search(pattern, text_lower)
        if match:
            return int(match.group(1))
    
    # Count job entries as fallback
    job_entries = len(re.findall(r'\b(?:job|position|role|experience)\b', text_lower))
    if job_entries > 5:
        return 5
    elif job_entries > 3:
        return 3
    elif job_entries > 1:
        return 1
    return 0

def calculate_skill_match(required_skills, resume_text):
    """Calculate skill match percentage with exact matching"""
    if not required_skills:
        return 0, [], []
    
    resume_lower = resume_text.lower()
    matched = []
    missing = []
    
    for skill in required_skills:
        skill_lower = skill.lower().strip()
        
        # Create word boundary pattern for exact matching
        # Escape special characters in skill name
        escaped_skill = re.escape(skill_lower)
        pattern = r'\b' + escaped_skill + r'\b'
        
        # Check if skill exists as a standalone word
        if re.search(pattern, resume_lower):
            matched.append(skill)
        else:
            # Check for common variations
            skill_variations = [skill_lower, skill_lower + 's', skill_lower + 'ing']
            found = False
            for variation in skill_variations:
                if re.search(r'\b' + re.escape(variation) + r'\b', resume_lower):
                    matched.append(skill)
                    found = True
                    break
            if not found:
                missing.append(skill)
    
    if len(required_skills) > 0:
        match_percentage = (len(matched) / len(required_skills)) * 100
    else:
        match_percentage = 0
    
    return match_percentage, matched, missing

def generate_candidate_insights(match_percentage, completeness_score, experience_years):
    """Generate professional insights"""
    insights = []
    
    if match_percentage >= 80:
        insights.append("• Exceptional technical alignment with position requirements")
    elif match_percentage >= 60:
        insights.append("• Strong technical foundation with some skill gaps identified")
    elif match_percentage >= 40:
        insights.append("• Moderate technical alignment; upskilling recommended")
    else:
        insights.append("• Limited technical alignment; significant skill development needed")
    
    if completeness_score >= 80:
        insights.append("• Well-documented professional profile with comprehensive information")
    elif completeness_score >= 60:
        insights.append("• Adequate documentation; additional details would strengthen profile")
    else:
        insights.append("• Incomplete profile; key sections missing")
    
    if experience_years >= 5:
        insights.append(f"• Senior-level professional with {experience_years}+ years of experience")
    elif experience_years >= 3:
        insights.append(f"• Mid-level professional with {experience_years}+ years of experience")
    elif experience_years >= 1:
        insights.append(f"• Early-career professional with {experience_years}+ years of experience")
    else:
        insights.append("• Entry-level candidate; strong potential for growth")
    
    return insights

# ---------------- MAIN ANALYSIS ----------------
if file is not None and role:
    try:
        file.seek(0)
        
        # Extract text
        if file.name.endswith(".pdf"):
            text = read_pdf(file)
        else:
            text = read_docx(file)
        
        # Show resume preview
        with st.expander("📄 Resume Content Preview", expanded=False):
            st.text_area("Document Content", text[:1000], height=200)
        
        # Get required skills
        required_skills = [s.strip() for s in required_skills_input.split(",") if s.strip()]
        
        # Calculate metrics
        match_percentage, matched_skills, missing_skills = calculate_skill_match(required_skills, text)
        completeness_score, sections = analyze_resume_completeness(text)
        experience_years = calculate_experience_years(text)
        extracted_skills = extract_skills_from_resume(text)
        
        # Generate insights
        insights = generate_candidate_insights(match_percentage, completeness_score, experience_years)
        
        # Professional Analysis Dashboard
        st.markdown("---")
        st.header("📊 Candidate Assessment Report")
        
        # Key Metrics Row
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Technical Compatibility", f"{match_percentage:.0f}%", 
                     delta="High" if match_percentage >= 70 else "Moderate" if match_percentage >= 40 else "Low")
        with col2:
            st.metric("Profile Completeness", f"{completeness_score:.0f}%")
        with col3:
            st.metric("Experience Level", f"{experience_years} Years")
        with col4:
            st.metric("Identified Skills", len(extracted_skills))
        
        st.markdown("---")
        
               # Advanced Skills Analysis with SkillAnalyzer
        st.markdown("### 🧠 Advanced Skill Analysis")
        
        # Extract advanced skills using SkillAnalyzer
        skill_analysis = skill_analyzer.extract_skills(text)
        
        # Display skill categories
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.markdown("**📊 Skills by Category**")
            if skill_analysis["categories"]:
                for category, skills in list(skill_analysis["categories"].items())[:3]:
                    category_name = category.replace('_', ' ').title()
                    st.write(f"**{category_name}:**")
                    for skill in skills[:3]:
                        st.write(f"  • {skill.title()}")
                    if len(skills) > 3:
                        st.write(f"  +{len(skills)-3} more")
            else:
                st.write("No skills detected")
        
        with col2:
            st.markdown("**📈 Skill Statistics**")
            st.write(f"**Total Skills:** {skill_analysis['total_count']}")
            st.write(f"**Categories:** {len(skill_analysis['categories'])}")
            
            # Show proficiency distribution
            if skill_analysis["skills"]:
                expert_count = sum(1 for s in skill_analysis["skills"] if s["proficiency"] == "expert")
                inter_count = sum(1 for s in skill_analysis["skills"] if s["proficiency"] == "intermediate")
                beginner_count = sum(1 for s in skill_analysis["skills"] if s["proficiency"] == "beginner")
                
                st.write(f"🟢 **Expert:** {expert_count}")
                st.write(f"🟡 **Intermediate:** {inter_count}")
                st.write(f"🔴 **Beginner:** {beginner_count}")
        
        with col3:
            st.markdown("**🎯 Match Analysis**")
            if required_skills:
                # Calculate advanced skill match
                skill_match_result = skill_analyzer.calculate_skill_match_advanced(
                    skill_analysis["skills"],
                    required_skills
                )
                
                st.write(f"**Match Score:** {skill_match_result['score']:.0f}%")
                st.write(f"**Matched:** {skill_match_result['match_count']}/{len(required_skills)}")
                
                # Update the match_percentage and matched_skills with advanced results
                match_percentage = skill_match_result['score']
                matched_skills = [s["name"] for s in skill_match_result['matched']]
                missing_skills = skill_match_result['missing']
            else:
                st.write("No skills specified")
        
        st.markdown("---")
        
        # Enhanced Verified Competencies with Proficiency
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("### ✅ Verified Competencies (with Proficiency)")
            if skill_match_result and skill_match_result.get('matched'):
                # Group by proficiency
                expert_skills = [s for s in skill_match_result['matched'] if s.get('proficiency') == 'expert']
                inter_skills = [s for s in skill_match_result['matched'] if s.get('proficiency') == 'intermediate']
                beginner_skills = [s for s in skill_match_result['matched'] if s.get('proficiency') == 'beginner']
                
                if expert_skills:
                    st.markdown("**🟢 Expert Level:**")
                    for skill in expert_skills:
                        st.write(f"  • {skill['name'].title()}")
                
                if inter_skills:
                    st.markdown("**🟡 Intermediate Level:**")
                    for skill in inter_skills:
                        st.write(f"  • {skill['name'].title()}")
                
                if beginner_skills:
                    st.markdown("**🔴 Beginner Level:**")
                    for skill in beginner_skills:
                        st.write(f"  • {skill['name'].title()}")
            else:
                st.write("• No matching competencies identified")
            
            st.markdown("### 🛠️ All Extracted Technical Skills")
            if skill_analysis["skills"]:
                # Show all extracted skills with proficiency
                for skill in skill_analysis["skills"][:10]:
                    prof_icon = "🟢" if skill['proficiency'] == 'expert' else "🟡" if skill['proficiency'] == 'intermediate' else "🔴" if skill['proficiency'] == 'beginner' else "⚪"
                    st.write(f"{prof_icon} {skill['name'].title()} - *{skill['proficiency'].title()}*")
                if len(skill_analysis["skills"]) > 10:
                    st.write(f"... and {len(skill_analysis['skills'])-10} more")
            else:
                st.write("• No technical skills detected")
        
        with col2:
            st.markdown("### ❌ Development Areas")
            if missing_skills:
                for skill in missing_skills[:5]:
                    st.write(f"• {skill.title()}")
                if len(missing_skills) > 5:
                    st.write(f"• ... and {len(missing_skills)-5} more")
            else:
                st.write("• No significant gaps identified")
            
            st.markdown("### 📚 Learning Recommendations")
            if missing_skills:
                recommendations = skill_analyzer.suggest_learning_path(missing_skills)
                for rec in recommendations[:3]:
                    priority_icon = "🔥" if rec["priority"] == 1 else "📘" if rec["priority"] == 2 else "📖"
                    st.write(f"{priority_icon} **{rec['skill'].title()}**")
                    st.write(f"   ⏱️ {rec['estimated_time']}")
                    st.write(f"   📖 {rec['resources'][0]}")
            else:
                st.write("• No learning recommendations needed")
            
            st.markdown("### 📋 Profile Completeness")
            for section, present in sections.items():
                status = "✅" if present else "❌"
                st.write(f"{status} {section.replace('_', ' ').title()}")


               # Enhanced Compatibility Score Visualization
        st.markdown("---")
        st.markdown("### 🎯 Overall Compatibility Assessment")
        
        # Add proficiency-weighted score explanation
        st.markdown("**Score includes proficiency weighting:** Expert skills contribute more to final score")
        
        if match_percentage >= 70:
            st.success(f"**{match_percentage:.0f}% Compatible** - Strong alignment with position requirements")
            st.progress(match_percentage/100)
            
            # Add proficiency insight
            if skill_match_result and skill_match_result.get('matched'):
                expert_skills = [s for s in skill_match_result['matched'] if s.get('proficiency') == 'expert']
                if expert_skills:
                    st.info(f"💪 **Strength:** Expert-level proficiency detected in {len(expert_skills)} critical skills including {expert_skills[0]['name'].title()}")
            
            st.info("**Recommendation:** Proceed to interview stage. Candidate demonstrates strong technical capabilities with advanced proficiency in key areas.")
            
        elif match_percentage >= 40:
            st.warning(f"**{match_percentage:.0f}% Compatible** - Moderate alignment with position requirements")
            st.progress(match_percentage/100)
            
            # Suggest focus areas
            if missing_skills:
                st.info(f"🎯 **Focus Areas:** Prioritize developing {', '.join(missing_skills[:3])}")
            
            st.info("**Recommendation:** Consider for further assessment. Some skill gaps identified that can be addressed through targeted training.")
            
        else:
            st.error(f"**{match_percentage:.0f}% Compatible** - Limited alignment with position requirements")
            st.progress(match_percentage/100)
            
            # Show learning path
            if missing_skills:
                st.info(f"📚 **Learning Path:** Recommended to start with {missing_skills[0].title()} as foundational skill")
            
            st.info("**Recommendation:** Consider alternative positions or enroll in skill development program.")
        
               # Enhanced Configuration Dashboard
            with st.expander("⚙️ Evaluation Configuration & Advanced Metrics", expanded=False):
             st.markdown(f"""
            ### Position Details
            - **Role:** {role}
            - **Required Competencies:** {', '.join(required_skills) if required_skills else 'Not specified'}
            
            ### Active Evaluation Criteria
            - Professional Experience: {'✅ Active' if use_experience else '❌ Inactive'}
            - Educational Background: {'✅ Active' if use_education else '❌ Inactive'}
            - Professional Certifications: {'✅ Active' if use_certifications else '❌ Inactive'}
            - Project Portfolio: {'✅ Active' if use_projects else '❌ Inactive'}
            
            ### Advanced Skill Metrics
            - **Total Skills Extracted:** {skill_analysis['total_count']}
            - **Skill Categories:** {len(skill_analysis['categories'])}
            - **Expert Level Skills:** {sum(1 for s in skill_analysis['skills'] if s['proficiency'] == 'expert')}
            - **Intermediate Level Skills:** {sum(1 for s in skill_analysis['skills'] if s['proficiency'] == 'intermediate')}
            - **Beginner Level Skills:** {sum(1 for s in skill_analysis['skills'] if s['proficiency'] == 'beginner')}
            
            ### Bias Mitigation Protocol
            - **Mode:** {mode}
            - De-identified Factors: Gender, Age, Institution, Location, Personal Identifiers
            """)