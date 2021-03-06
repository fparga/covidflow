from typing import Any, Dict, List, Text

from rasa_sdk import Action, Tracker
from rasa_sdk.executor import CollectingDispatcher

from .constants import SELF_ASSESS_DONE_SLOT
from .lib.log_util import bind_logger


class ActionAskTestNavigationContinueError(Action):
    def name(self) -> Text:
        return "action_ask_test_navigation__continue_error"

    def run(
        self,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: Dict[Text, Any],
    ) -> List[Dict[Text, Any]]:
        bind_logger(tracker)
        if tracker.get_slot(SELF_ASSESS_DONE_SLOT) is True:
            dispatcher.utter_message(
                template="utter_ask_test_navigation__continue_error_no_assessment"
            )
        else:
            dispatcher.utter_message(
                template="utter_ask_test_navigation__continue_error_offer_assessment"
            )

        return []
