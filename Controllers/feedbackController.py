from fastapi import Request, HTTPException
from fastapi.responses import JSONResponse
import pandas as pd
import numpy as np
from Utils.common import CommonFunctions
from Controllers.llmGenerationController import LLMGenerationController
import asyncio




class FeedbackController:
    def get_feedback_data_excel(self,file):
        try:
            if file is None or file.file is None:
                return JSONResponse(
                    status_code=400,
                    content={"message": "File is required."}
                )

            df = pd.read_excel(file.file)
            df = df.replace([np.nan, np.inf, -np.inf], None)
            for col in df.columns:
                if pd.api.types.is_datetime64_any_dtype(df[col]):
                    df[col] = df[col].astype(str)

            data = df.to_dict(orient="records")

            name=data[0].get('Employee Name') or data[0].get('Name') or 'Employee Name'
            right_culture = [
                row for row in data if row.get("Name") == "Creating the Right Culture"
            ]
            leadership_style = [
                row for row in data if row.get("Name") == "Leadership Style"
            ]
            leadership_staff_dev = [
                row for row in data if row.get("Name") == "Leadership for Staff Performance & Development"
            ]
            educational_quality = [
                row for row in data if row.get("Name") == "Educational Quality & Student Outcomes"
            ]
            engagement_with_management = [
                row for row in data if row.get("Name") == "Engagement with Management"
            ]
            general = [
                row for row in data if row.get("Name") == "General"
            ]

            right_culture_competency = CommonFunctions.questionwise_avg_by_rate_group(right_culture)
            leadership_style_competency = CommonFunctions.questionwise_avg_by_rate_group(leadership_style)
            leadership_staff_dev_competency = CommonFunctions.questionwise_avg_by_rate_group(leadership_staff_dev)
            educational_quality_competency = CommonFunctions.questionwise_avg_by_rate_group(educational_quality)
            engagement_with_management_competency = CommonFunctions.questionwise_avg_by_rate_group(engagement_with_management)

            overall_questionwise_data = {}

            overall_questionwise_data.update(right_culture_competency)
            overall_questionwise_data.update(leadership_style_competency)
            overall_questionwise_data.update(leadership_staff_dev_competency)
            overall_questionwise_data.update(educational_quality_competency)
            overall_questionwise_data.update(engagement_with_management_competency)

            general_competency=CommonFunctions.grouped_question(general)
            abc_questions=CommonFunctions.count_abc_responses(general_competency)
            workplace_culture=CommonFunctions.get_workplace_culture_data(general_competency,"workplace culture")
            stand_out_leader_thing=CommonFunctions.get_workplace_culture_data(general_competency,'stand out as a leader')
            continue_doing_thing=CommonFunctions.get_workplace_culture_data(general_competency,'do more often or keep doing')
            stop_altogether=CommonFunctions.get_workplace_culture_data(general_competency,'stop altogether')
            action_areas_thing_data=CommonFunctions.get_workplace_culture_data(general_competency,'differently, adjust or change to improve')

            workplace_culture_words=CommonFunctions.count_workplace_culture_words(workplace_culture)
            stand_out_leader_thing_words=CommonFunctions.count_workplace_culture_words(stand_out_leader_thing)
            continue_doing_thing_words=CommonFunctions.get_non_self_comments(continue_doing_thing)
            stop_doing_thing_words=CommonFunctions.get_non_self_comments(stop_altogether)
            predominant_leader_thing=CommonFunctions.get_non_self_comments(stand_out_leader_thing)
            action_areas_thing_data_comment=CommonFunctions.get_non_self_comments(action_areas_thing_data)
            
            action_areas_thing_data_extended = []
            action_areas_thing_data_extended.append(stand_out_leader_thing_words)
            action_areas_thing_data_extended.append(continue_doing_thing_words)
            action_areas_thing_data_extended.append(stop_doing_thing_words)
            action_areas_thing_data_extended.extend(action_areas_thing_data_comment)
            controller = LLMGenerationController()
            analysis_data={
                    "continue_doing": continue_doing_thing_words,
                    "stop_doing": stop_doing_thing_words,
                    "predominant_leader_thing": predominant_leader_thing
                }
            
            continue_prompt = """
You are a STRICT Educational Feedback Formatter.

OBJECTIVE:
Return ONLY clearly positive comments.

FILTERING RULES:
Keep a comment ONLY if it clearly expresses:
- Appreciation
- Strength
- Encouragement
- Positive quality
- Good practice
- Constructive positive expectation

REMOVE completely:
- Negative comments
- Complaints
- Criticism
- Neutral statements
- Mixed sentiment (positive + negative together)
- "-", "---"
- "Nil", "NIL"
- "no comment", "no comments"
- "nothing"
- Empty text
- Anything unclear in sentiment

CORE RULE:
INPUT COMMENT = OUTPUT COMMENT.
Do NOT rewrite, rephrase, expand, shorten, or add new words.
Do NOT change sentence structure.

ALLOWED:
- Fix very minor grammar or spacing issues only.
- Apply Markdown bold (**text**) ONLY to clearly positive traits or qualities that already exist in the sentence.
- Do NOT invent new words for bolding.
- Do NOT bold the entire sentence unless the full sentence is purely a positive trait.

IMPORTANT:
- If a comment is not clearly positive → REMOVE it completely.
- One valid input comment → exactly one output comment.
- Preserve original wording.
- Preserve order.

OUTPUT:
Return ONLY valid JSON:
{
  "continue_doing": [string]
}

No explanations.
Only JSON.
"""
            stop_prompt = """
You are a STRICT Educational Feedback Formatter.

TASK:
Return ONLY clearly negative comments.

REMOVE:
- Positive comments
- Neutral comments
- "-", "---"
- "Nil", "NIL"
- "no comment", "no comments"
- "nothing"
- Empty text
- Anything unclear in sentiment

If a comment is not clearly negative, REMOVE it.
Do NOT move comments.
Do NOT rewrite comments to make them negative.

CORE RULE:
INPUT COMMENT = OUTPUT COMMENT.
Do NOT rewrite, rephrase, expand, shorten, or add words.

ALLOWED:
- Fix minor grammar or spacing only
- Highlight ONLY explicit negative phrases using:
  <span style="color:red"><strong>negative phrase</strong></span>

OUTPUT:
Return ONLY valid JSON:
{
  "stop_doing": [string]
}
No explanations.
"""   
            predominant_prompt = """
You are a STRICT Educational Feedback Formatter.

OBJECTIVE:
Return ONLY clearly positive leadership qualities or traits for predominant_leader_thing.

FILTERING RULES:
Keep a comment ONLY if it clearly expresses:
- Positive leadership quality
- Strong character trait
- Appreciation of leadership style
- Supportive or fair leadership behavior
- Strength in management or guidance

REMOVE completely:
- Negative comments
- Complaints
- Criticism
- Neutral statements
- Advisory suggestions without clear appreciation
- Mixed sentiment (positive + negative together)
- "-", "---"
- "Nil", "NIL"
- "no comment", "no comments"
- "nothing"
- Empty text
- Anything unclear in sentiment

CORE RULE:
INPUT COMMENT = OUTPUT COMMENT.
Do NOT rewrite, rephrase, expand, shorten, or add words.
Do NOT change sentence structure.
Do NOT add prefixes like "Continue" or any other words.

ALLOWED:
- Fix very minor grammar or spacing issues only.
- Apply Markdown bold (**text**) ONLY to clearly positive leadership traits already written in the sentence.
- Do NOT invent new words for bolding.
- Do NOT bold the entire sentence unless the full sentence is purely a positive leadership trait.

IMPORTANT:
- If a comment is not clearly positive → REMOVE it completely.
- One valid input comment → exactly one output comment.
- Preserve original wording.
- Preserve order.

OUTPUT:
Return ONLY valid JSON:
{
  "predominant_leader_thing": [string]
}

No explanations.
Only JSON.
"""

            continue_feedback_schema = {
    "type": "object",
    "properties": {
        "continue_doing": {
            "type": "array",
            "items": {
                "type": "string"
            },
            "description": "Formatted comments describing practices to continue."
        },
       
    },
    "required": [
        "continue_doing",
    ],
}
            stop_feedback_schema = {
    "type": "object",
    "properties": {
        
        "stop_doing": {
            "type": "array",
            "items": {
                "type": "string"
            },
            "description": "Formatted comments describing practices to stop."
        },
        
    },
    "required": [
        
        "stop_doing"
        ]
      
}
            predominant_schema = {
    "type": "object",
    "properties": {
        
        "predominant_leader_thing": {
            "type": "array",
            "items": {
                "type": "string"
            },
            "description": "Formatted comments describing predominant leadership traits."
        }
    },
    "required": [
       
        "predominant_leader_thing"
    ]
}
            # action_areas_thing_llm_generate = controller.generate_action_areas(action_areas_thing_data_extended)
            # analysis_general_continue_doing = controller.analysis_comment_to_generate(continue_doing_thing_words,system_prompt=continue_prompt,feedback_schema=continue_feedback_schema)
            # analysis_general_stop_doing = controller.analysis_comment_to_generate(stop_doing_thing_words,system_prompt=stop_prompt,feedback_schema=stop_feedback_schema)
            # analysis_general_predominant_leader_thing = controller.analysis_comment_to_generate(predominant_leader_thing,system_prompt=predominant_prompt,feedback_schema=predominant_schema)
            action_areas_thing_llm_generate={ 
                "continue": [
            "Maintains clear, fair, and consistent policies, fostering discipline and security.",
            "Provides empathetic, supportive leadership, encouraging high performance and professional growth.",
            "Leads by example with commitment, strong vision, and effective, transparent communication."
        ],
        "start": [
            "Implement more frequent, personalized feedback and recognition for staff achievements.",
            "Foster greater collaboration and open communication, involving staff in decision-making processes.",
            "Introduce new training, workshops, and mentorship programs to enhance teaching skills and resources."
        ],
        "stop": [
            "Reduce micromanagement and excessive administrative tasks, delegating responsibilities effectively.",
            "Cease partiality or favouritism, ensuring fair and objective decision-making based on verified information.",
            "Avoid public criticism or negative comparisons, providing constructive feedback privately."
        ]
    }
                      
          
            return JSONResponse(
                status_code=200,
                content={
                    "name": name,
                    "competency_summary_overall":{
                     'leadership_style': CommonFunctions.overall_avg_by_group(leadership_style_competency),
                     'educational_quality': CommonFunctions.overall_avg_by_group(educational_quality_competency),
                     'leadership_staff_dev': CommonFunctions.overall_avg_by_group(leadership_staff_dev_competency),
                     'right_culture': CommonFunctions.overall_avg_by_group(right_culture_competency),
                     'engagement_with_management': CommonFunctions.overall_avg_by_group(engagement_with_management_competency)
                    },
                    "strengths": CommonFunctions.find_strengths_separately(overall_questionwise_data),
                    "area_of_improvement": CommonFunctions.find_area_of_improvement_separately(overall_questionwise_data),
                    "right_culture_competency": right_culture_competency,
                    "leadership_style_competency": leadership_style_competency,
                    "leadership_staff_dev_competency": leadership_staff_dev_competency,
                    "educational_quality_competency": educational_quality_competency,
                    "engagement_with_management_competency": engagement_with_management_competency,
                    "nominee_leadership":abc_questions,
                    "workplace_culture":workplace_culture_words,
                    "predominant_leader_most_thing":stand_out_leader_thing_words[:12],
                    # "continue_doing_thing":analysis_general_continue_doing['structured']['continue_doing'] if analysis_general_continue_doing['structured'] else [],
                    # "stop_doing_thing":analysis_general_stop_doing['structured']['stop_doing'] if analysis_general_stop_doing['structured'] else [],
                    # "predominant_leader_thing":analysis_general_predominant_leader_thing['structured']['predominant_leader_thing'] if analysis_general_predominant_leader_thing['structured'] else [],
                    # "action_areas_thing":action_areas_thing_llm_generate['structured']
                     "action_areas_thing":action_areas_thing_llm_generate,
                    "continue_doing_thing":[
    "**Come on rounds**",
    "**Needed to give feedback**",
    "When I have given option for whatever about our Art work..mam **immediately responded**",
    "**Encouragement**",
    "**Clear, fair, and consistent policies** ensure that all students and staff understand expectations and feel secure in the environment. **Clear, fair, and consistent policies** ensure that all students and staff understand expectations and feel secure in the environment. **Clear, fair, and consistent policies** ensure that all students and staff understand expectations and feel secure in the environment.",
    "**Encourage open communication** and **actively seek feedback** from students, teachers, and parents to ensure everyone's voice is heard and valued.",
    "**Give ears to all equally**",
    "**On the spot recognition**",
    "Please Appoint **well trained and efficient teachers with good communication skills** for primary as the foundational education plays a vital role",
    "**Workshops on different topics**, **visiting classrooms**, having **meetings often**",
    "**Praise one's efforts**, wherever it is **deserving, openly**.",
    "**Motivating teachers**",
    "**Focus more on effective teaching learning process**.",
    "**Encourage open communication**.",
    "**Need to motivate and encourage the team more positively** to improve the confidence.",
    "**Cleanliness**",
    "She should continue to **interact with her team to resolve hurdles**.",
    "**Regular communication with students and staffs**",
    "**Motivating English language communication skills** for both teachers and students.",
    "**Giving us ample time with children to enrich academic transactions**",
    "**Frequent feedback**. It helps us understand our current performance and identify areas for improvement.",
    "Our principal is **committed towards her duty**, which is why she hardly takes leave. This act of hers sets an example to all the staff members.",
    "**Punctuality**",
    "Ma'am takes **great interest in students' academic progress and co-curricular activities**. She **appreciates their individual learning styles**. She does this for teachers as well.",
    "I think the Principal is already doing a **fantastic job supporting teachers**. The Principal has been a **strong and supportive leader**, always **encouraging both personal and professional growth**. If anything, **more frequent recognition of teachers' efforts and achievements** would further boost morale and foster a positive environment.",
    "**Giving feedback for continuous development**.",
    "**Introspect the decisions**.",
    "**Appreciation and encouragement**",
    "The strategy of **decision making** by the principal at tight corner has always been **effective** and has also **positively impacted** me, hence I would ask the principle to abide it.",
    "**Availability of resources & new technical aids**",
    "**Encourage**",
    "**Approachable**",
    "She does everything in an **organised manner**, writes down everything and plans to finish all the tasks on time or even before the dead line. The way she **praises and speaks politely** and also to the point.",
    "**Providing appropriate Appreciation and feedback whenever needed**",
    "**Regular feedback**. This will help us where we stand and what to improve.",
    "Ma'am **ensures that we are never required to wait outside her office under any circumstances**.",
    "**Motivating**",
    "The principal **ensures that we are never required to wait outside her office under any circumstances**.",
    "To give **more appreciation and rewards to the work done**",
    "Principal ma'am always **guides us to do our work even more effectively** which helps us a lot.",
    "**Encouraging positive feedback** which **motivates to work with enthusiasm in achieving the goal**",
    "More time can be given for academics than the extra curricular activities especially for class 11 and 12.",
    "**Encourage**",
    "**To motivate others**",
    "I would ask to provide **more support to teachers**, such as **open discussions to address concerns and challenges**, as this would help create a **more collaborative and encouraging environment**",
    "**Good leadership** and **approachable**",
    "She is always **motivating us**.",
    "**Appreciate the efforts of the staff**",
    "**Appreciation**",
    "I would like her to continue **encouraging all the languages and subjects with equal importance**.",
    "**Encourage collaboration among teachers**",
    "**Prompt feedback, encouragement, team/school events**",
    "To have **more one on one meets and feedback sessions** as its **motivating** and keeps us on track.",
    "**Result oriented**",
    "Principal ma'am always gives as **clear communication** and remainder of every task to be completed by on-time."
],
                    "stop_doing_thing":[
    "<span style=\"color:red\"><strong>Shout in public</strong></span>",
    "Focus less on <span style=\"color:red\"><strong>excessive administrative tasks or micromanagement</strong></span> and prioritize being present and engaged with students and staff.",
    "<span style=\"color:red\"><strong>Not to be partial</strong></span>",
    "<span style=\"color:red\"><strong>Not to judge the people with one incident</strong></span>",
    "Treat everyone equally and <span style=\"color:red\"><strong>not be partial to a particular community</strong></span>. Make judgement about teachers by understanding them and rating them by their quality of work and <span style=\"color:red\"><strong>not by listening to others</strong></span>.",
    "To <span style=\"color:red\"><strong>discuss about co-worker's mistakes</strong></span>",
    "<span style=\"color:red\"><strong>Too lenient</strong></span>",
    "I might suggest doing less of <span style=\"color:red\"><strong>overthinking or being overly cautious in decision-making</strong></span>.",
    "<span style=\"color:red\"><strong>Stop reacting for small issues</strong></span>",
    "<span style=\"color:red\"><strong>Stop reacting for the minor problems spread through air</strong></span>.",
    "If someone says something, that info is to be <span style=\"color:red\"><strong>verified before accusing someone</strong></span>.",
    "Ma'am can delegate responsibilities to different teams to reduce her burden. She is <span style=\"color:red\"><strong>shouldering too much responsibility</strong></span>.",
    "<span style=\"color:red\"><strong>Biased beliefs</strong></span>.",
    "<span style=\"color:red\"><strong>Micromanage</strong></span>",
    "<span style=\"color:red\"><strong>Should not believe in one person</strong></span>",
    "<span style=\"color:red\"><strong>Not to criticise or give harsh negative comments in front of peers</strong></span>",
    "<span style=\"color:red\"><strong>Not being flexible</strong></span>.",
    "More number of tasks <span style=\"color:red\"><strong>should not be given to the same person</strong></span>",
    "I would ask the principal to reduce <span style=\"color:red\"><strong>micromanaging or unrealistic expectations without providing adequate support</strong></span>, as this adds unnecessary pressure and impacts the overall morale of the teaching staff.",
    "Reduce <span style=\"color:red\"><strong>work pressure</strong></span>",
    "A principal must <span style=\"color:red\"><strong>avoid taking decision solely on others' opinion</strong></span>. Instead relevant information can be gathered, listen to others' perspective and approach situations to ensure fair decision making.",
    "<span style=\"color:red\"><strong>Cease exhibiting favouritism towards individual</strong></span>",
    "Can reschedule school events for more gap between exams and events"
],
                    "predominant_leader_thing":[
    "**Supportive**",
    "She **encourages to do the best in us**.",
    "She is **very confident in her decisions** and has a **good command to bring discipline in school**",
    "**Transparent in her views**",
    "**Speaks in soft tone how much ever the bad situation is**",
    "A Principal who **leads by example**, consistently demonstrating a **strong vision, empathy, and commitment** to the school community can foster a positive culture.",
    "**Provides enough support, direction and guidance whenever required**, for effective performance of team members",
    "**Very knowledgeable** and **actions taken correctly on time**",
    "**Motivation**",
    "**Kindness**",
    "**Good memory**",
    "**Balancing professional and personal relationships**",
    "Her **commitment towards the organization**.",
    "She **understands and helps everyone when we need guidance**",
    "A principal should **inspire and celebrate her students and staff by regularly recognizing and appreciating them**. Give **ample support, feedback, trust** and foster a **culture of excellence and productivity**",
    "**Inspiring shared vision**.",
    "**Incredible documentation and follow up of the tasks in the school**",
    "**Disciplined**",
    "She is on the verge of retirement and I personally feel, she has done a **good job**. I wish her a healthy and happy retired life.",
    "**Setting clear goals** and making **effective decisions**.",
    "Principal is **effective in communication** and she is **well organized with great managing skills** to be a leader.",
    "**Individuality**",
    "**Consistently maintains a professional demeanor** with her team and parents.",
    "Our principal has 28 + years of teaching/ managing everyone **perfectly as a head**. She is **very well approachable** for seeking help or solving any problem or in case of doubts. She is truly a **leader with such great experience**. In a given institution, the principal should be **approachable by the staff** which is very important.",
    "Ma'am stresses the importance of **considering others' opinion/ ideas** in all her school transactions.",
    "The Principal's **commitments to the growth of both staff and students through ongoing learning and development opportunities is truly unique**.",
    "She is a **dynamic and assertive person**. She is **quick to act**.",
    "**Sweet spoken**",
    "**Treating everyone equally**",
    "She has **never made anyone feel uncomfortable raising her voice**.",
    "**Leadership skills, decision making, friendly nature**.",
    "**Easily approachable and amicable**",
    "**Democratic**",
    "**Polite, humble and kind**",
    "The way she always ** appreciates when things are done right** and also points out the mistakes with a **good intention** that we should not repeat it again. She always insists that whatever is done its for the students.",
    "**Analyzing each problem on both sides in presence of both individuals**.",
    "**Always behaves in a professional manner with her team and parents**.",
    "**Strong ability to guide and motivate staff and students** fostering a **positive school environment**.",
    "**Dedication, Determination, Supporting**",
    "As a **good leader** ma'am **listens to others and shows genuine interest in what they have to say**.",
    "**Immediate addressing of any issue arising in the school**",
    "Ma'am never missed to **appreciate a teacher who works good** and she always **encourage us to work as a team**.",
    "**Credible, fair and consistent in their judgement**, give the employees the **opportunities to be their best**.",
    "She stands in her **own individuality**.",
    "**Leadership skills**",
    "**Supportive**",
    "**Very understanding and good human being**",
    "**Workaholic**",
    "**Warmth, humane**",
    "**Approachable**.",
    "**Ability to inspire and motivate others, empathetic, empower everyone to reach their full potential** which in turn will contribute to school's growth.",
    "Her **dedication and work ethic** makes her stand out.",
    "**Possess exceptional long-term memory**",
    "**Speaks politely to all**",
    "She is **very approachable**. This makes our work place **stress free** and **improves our performance**. She has **empathy towards everybody**.",
    "**Focus on understanding the needs of others**",
    "**Very efficient**",
    "**Easy approachable and listen to other concerns**. We are really going to miss our Principal for the next academic year."
],
                     
                }
            )
                

        except Exception as e:
            return JSONResponse(
                status_code=500,
                content={"message": f"Error : {str(e)}"}
            )