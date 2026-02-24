from fastapi import Request, HTTPException
from fastapi.responses import JSONResponse
import pandas as pd
import numpy as np
from Utils.common import CommonFunctions

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
            action_areas_thing=CommonFunctions.categorize_comments(action_areas_thing_data)
          
            return JSONResponse(
                status_code=200,
                content={
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
                    "continue_doing_thing":continue_doing_thing_words,
                    "stop_doing_thing":stop_doing_thing_words,
                    "predominant_leader_thing":predominant_leader_thing,
                    "action_areas_thing":action_areas_thing
                }
            )
                

        except Exception as e:
            return JSONResponse(
                status_code=500,
                content={"message": f"Error : {str(e)}"}
            )