
from collections import defaultdict
import re
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

class CommonFunctions:
    @staticmethod
    def grouped_question(records):
        question_grouped = defaultdict(list)

        for row in records:
            question = row.get("Question")
            if not question:
                continue
            question_grouped[question].append(row)

        return question_grouped


    @staticmethod
    def questionwise_avg_by_rate_group(records):
        question_grouped = defaultdict(list)

        for row in records:
            question = row.get("Question")
            if not question:
                continue
            question_grouped[question].append(row)

        final_output = {}

        for question, rows in question_grouped.items():
            grouped = defaultdict(list)

            for item in rows:
                group = item.get("Rater Group")
                value = item.get("Rating")

                if group is None or value is None:
                    continue

                grouped[group].append(value)

            avg_result = {}

            sub_vals = grouped.get("Subordinates", [])
            oth_vals = grouped.get("Others", [])

            combined_people = sub_vals + oth_vals
            if combined_people:
                avg_result["Subordinates"] = round(
                    sum(combined_people) / len(combined_people), 2
                )

            l1_vals = grouped.get("L1 Manager", [])
            l2_vals = grouped.get("L2 Manager", [])

            combined_mgr = l1_vals + l2_vals
            if combined_mgr:
                avg_result["Manager"] = round(
                    sum(combined_mgr) / len(combined_mgr), 2
                )

            for group, values in grouped.items():
                if group in ["Subordinates", "Others", "L1 Manager", "L2 Manager"]:
                    continue

                avg_result[group] = round(sum(values) / len(values), 2)

            final_output[question] = avg_result

        return final_output


    @staticmethod
    def overall_avg_by_group(questionwise_data):
        grouped = defaultdict(list)

        for question, groups in questionwise_data.items():
            for group, value in groups.items():
                if value is None:
                    continue
                grouped[group].append(value)

        final_avg = {}
        for group, values in grouped.items():
            final_avg[group] = round(sum(values) / len(values), 2)

        return final_avg


    @staticmethod
    def find_strengths_separately(questionwise_data):
        sub_strengths = []
        mgr_strengths = []

        for question, groups in questionwise_data.items():
            sub_val = groups.get("Subordinates")
            mgr_val = groups.get("Manager")

            if sub_val is not None and sub_val > 4.5:
                sub_strengths.append({
                    "question": question,
                    "score": sub_val
                })

            if mgr_val is not None and mgr_val > 4:
                mgr_strengths.append({
                    "question": question,
                    "score": mgr_val
                })

        sub_strengths.sort(key=lambda x: x["score"], reverse=True)
        mgr_strengths.sort(key=lambda x: x["score"], reverse=True)

        return {
            "Subordinates": sub_strengths[:3],
            "Manager": mgr_strengths[:3]
        }

    @staticmethod
    def find_area_of_improvement_separately(questionwise_data):
        sub_strengths = []
        mgr_strengths = []

        for question, groups in questionwise_data.items():
            sub_val = groups.get("Subordinates")
            mgr_val = groups.get("Manager")

            if sub_val is not None and sub_val < 4.5:
                sub_strengths.append({
                    "question": question,
                    "score": sub_val
                })

            if mgr_val is not None and mgr_val < 4:
                mgr_strengths.append({
                    "question": question,
                    "score": mgr_val
                })

        sub_strengths.sort(key=lambda x: x["score"])
        mgr_strengths.sort(key=lambda x: x["score"])

        return {
            "Subordinates": sub_strengths[:3],
            "Manager": mgr_strengths[:3]
        }


    @staticmethod
    def detect_option(comment_clean, option_map, threshold=0.3):
        """
        Detect option using cosine similarity
        """
        texts = list(option_map.values())
        letters = list(option_map.keys())

        corpus = [comment_clean] + texts

        vectorizer = TfidfVectorizer().fit_transform(corpus)
        vectors = vectorizer.toarray()

        comment_vector = vectors[0]
        option_vectors = vectors[1:]

        similarities = cosine_similarity([comment_vector], option_vectors)[0]

        best_index = similarities.argmax()
        best_score = similarities[best_index]

        if best_score >= threshold:
            return letters[best_index]

        return None


    @staticmethod
    def count_abc_responses(data):
        if not data:
            return {}

        question, records = next(iter(data.items()))

        question_clean = question.replace("_x000D_", "").strip()
        option_pattern = re.findall(
            r"(?:^|\n)\s*([A-C])\)\t([^\n]+)(?:_x000D_)?",
            question_clean,
            re.DOTALL
        )
        if not option_pattern:
            return {}

        option_map = {}
        for letter, text in option_pattern:
            option_map[letter.upper()] = text.strip().lower()

        option_counts = defaultdict(int)

        for item in records:
            comment = item.get("Comment")
            if not comment:
                continue

            comment_clean = comment.strip().lower()
            detected_option = None
            letter_match = re.search(
                r"\b(" + "|".join(option_map.keys()) + r")\b",
                comment_clean,
                re.IGNORECASE
            )

            if letter_match:
                detected_option = letter_match.group(1).upper()

            if not detected_option:
                for letter, option_text in option_map.items():
                    if option_text in comment_clean:
                        detected_option = letter
                        break

            if not detected_option:
                detected_option = CommonFunctions.detect_option(
                    comment_clean,
                    option_map,
                    threshold=0.3
                )

            if detected_option:
                option_counts[detected_option] += 1

        for opt in option_map.keys():
            option_counts.setdefault(opt, 0)

        per_option = {}
        for letter, text in option_map.items():
            per_option[letter] = {
                "text": text.capitalize(),
                "count": option_counts.get(letter, 0)
            }

        return per_option


    @staticmethod
    def get_workplace_culture_data(data,question_type):
        for question, records in data.items():
            if  question_type in question.lower():
                return records
        return []

    @staticmethod
    def count_workplace_culture_words(records):
        word_counts = defaultdict(int)

        for item in records:
            comment = item.get("Comment")
            if not comment or comment == "nil":
                continue

            words = comment.split(",")

            for word in words:
            
                    clean_word = word.strip().lower()

                    clean_word = re.sub(r"[^\w\s-]", "", clean_word)

                    if clean_word and clean_word !='nil' :
                        word_counts[clean_word] += 1

        sorted_items = sorted(word_counts.items(), key=lambda x: x[1], reverse=True)[:15]
        top_words = [word for word, _ in sorted_items]
        return top_words

    @staticmethod
    def get_non_self_comments(records):
        comments = []

        for item in records:
            if item.get("Rater Group") == "Self":
                continue

            comment = item.get("Comment")
            # ignore_values = {"nil", "-", "no comment", "no comments", "na", "none"}
            if comment and comment.strip() :
                comments.append(comment.strip())

        return comments


    @staticmethod
    def classify_comment_text(comment: str) -> str:
        """Classify a single comment as Start / Stop / Continue / Uncategorized."""
        if not comment:
            return " uncategorized"

        text = comment.lower()

        continue_keywords = ["happy", "great", "open", "positive", "appreciate"]
        start_keywords = ["more", "foster", "increase", "improve", "start", "encourage"]
        stop_keywords = ["not", "stop", "avoid", "reduce", "don't"]

        if any(word in text for word in stop_keywords):
            return "stop"
        elif any(word in text for word in start_keywords):
            return "start"
        elif any(word in text for word in continue_keywords):
            return "continue"
        else:
            return "uncategorized"


    @staticmethod
    def categorize_comments(records):
        """Group comments from records into Start/Stop/Continue/Uncategorized, ignoring nil/no-comment style values."""
        categories = {
            "start": [],
            "stop": [],
            "continue": [],
            "uncategorized": [],
        }

        ignore_values = {"nil", "-", "no comment", "no comments", "na", "n/a"}

        for item in records:
            comment = item.get("Comment")
            if not comment:
                continue

            cleaned = comment.strip()
            if not cleaned:
                continue

            if cleaned.lower() in ignore_values:
                continue

            bucket = CommonFunctions.classify_comment_text(cleaned)
            categories[bucket].append(cleaned)

        return categories