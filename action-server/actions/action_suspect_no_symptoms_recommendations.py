from typing import Any, Dict, List, Text

from rasa_sdk import Action, Tracker
from rasa_sdk.executor import CollectingDispatcher


class ActionSuspectNoSymptomsRecommendations(Action):
    def name(self) -> Text:
        return "action_suspect_no_symptoms_recommendations"

    def run(
        self,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: Dict[Text, Any],
    ) -> List[Dict[Text, Any]]:

        dispatcher.utter_message(template="utter_probably_not_covid")
        dispatcher.utter_message(template="utter_social_distancing")
        dispatcher.utter_message(template="utter_checkin_if_developments")

        return []