from typing import Any, Dict, List, Optional, Text, Union

from rasa_sdk import Tracker
from rasa_sdk.events import EventType
from rasa_sdk.executor import CollectingDispatcher
from rasa_sdk.forms import FormAction

from covidflow.utils.persistence import cancel_reminder

from .constants import (
    AGE_OVER_65_SLOT,
    CANCEL_CI_SLOT,
    FEEL_WORSE_SLOT,
    PRECONDITIONS_SLOT,
    PROVINCE_SLOT,
    PROVINCES_WITH_211,
    SYMPTOMS_SLOT,
    Symptoms,
)
from .form_helper import request_next_slot
from .lib.log_util import bind_logger

FORM_NAME = "daily_ci_keep_or_cancel_form"

DEFAULT_INFO_LINK = "https://covid19.dialogue.co/#/info?id=common"


class DailyCiKeepOrCancelForm(FormAction):
    def name(self) -> Text:

        return FORM_NAME

    async def run(
        self, dispatcher, tracker, domain,
    ):
        bind_logger(tracker)
        return await super().run(dispatcher, tracker, domain)

    ## override to play initial message
    async def _activate_if_required(
        self,
        dispatcher: "CollectingDispatcher",
        tracker: "Tracker",
        domain: Dict[Text, Any],
    ) -> List[EventType]:
        if (
            tracker.active_form.get("name") != FORM_NAME
            and tracker.get_slot(SYMPTOMS_SLOT) == Symptoms.NONE
        ):
            dispatcher.utter_message(
                template="utter_daily_ci__keep_or_cancel__no_symptoms_recommendation"
            )

        return await super()._activate_if_required(dispatcher, tracker, domain)

    @staticmethod
    def required_slots(tracker: Tracker) -> List[Text]:
        """A list of required slots that the form has to fill"""

        return [] if _mandatory_ci(tracker) else [CANCEL_CI_SLOT]

    def slot_mappings(self) -> Dict[Text, Union[Dict, List[Dict]]]:
        return {
            CANCEL_CI_SLOT: [
                self.from_intent(intent="cancel", value=True),
                self.from_intent(intent="continue", value=False),
            ],
        }

    def request_next_slot(
        self,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: Dict[Text, Any],
    ) -> Optional[List[EventType]]:
        return request_next_slot(
            self, dispatcher, tracker, domain, self._utter_ask_slot_template
        )

    def _utter_ask_slot_template(self, slot: str, tracker: Tracker) -> Optional[str]:
        if slot == CANCEL_CI_SLOT:
            if tracker.get_slot(SYMPTOMS_SLOT) == Symptoms.NONE:
                return f"utter_ask_daily_ci__keep_or_cancel__{slot}_no_symptoms"
            else:
                return f"utter_ask_daily_ci__keep_or_cancel__{slot}_symptoms"

        return None

    def submit(
        self,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: Dict[Text, Any],
    ) -> List[Dict]:
        # Mandatory check-in
        if _mandatory_ci(tracker):
            dispatcher.utter_message(
                template="utter_daily_ci__keep_or_cancel__feel_worse_keep_ci"
            )
            dispatcher.utter_message(
                template="utter_daily_ci__keep_or_cancel__feel_worse_recommendation"
            )
            _recommendations(dispatcher, tracker, domain)

        # Optional check-in cancel
        elif tracker.get_slot(CANCEL_CI_SLOT) is True:
            dispatcher.utter_message(
                template="utter_daily_ci__keep_or_cancel__acknowledge_cancel_ci"
            )
            dispatcher.utter_message(
                template="utter_daily_ci__keep_or_cancel__cancel_ci_recommendation"
            )
            try:
                cancel_reminder(tracker.current_slot_values())
            except:
                pass
        else:
            # Optional check-in continue
            dispatcher.utter_message(
                template="utter_daily_ci__keep_or_cancel__acknowledge_continue_ci"
            )

            if tracker.get_slot(SYMPTOMS_SLOT) != Symptoms.NONE:
                _recommendations(dispatcher, tracker, domain)

        return []


def _mandatory_ci(tracker: Tracker) -> bool:
    if tracker.get_slot(SYMPTOMS_SLOT) == Symptoms.NONE:
        return False

    if tracker.get_slot(FEEL_WORSE_SLOT) is True:
        return (
            tracker.get_slot(SYMPTOMS_SLOT) == Symptoms.MODERATE
            or tracker.get_slot(PRECONDITIONS_SLOT) is True
            or tracker.get_slot(AGE_OVER_65_SLOT) is True
        )

    return False


def _recommendations(
    dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict[Text, Any]
) -> None:
    provincial_link = _get_provincial__info_link(tracker, domain)
    if (
        tracker.get_slot(AGE_OVER_65_SLOT) is True
        or tracker.get_slot(PRECONDITIONS_SLOT) is True
    ):
        dispatcher.utter_message(
            template="utter_daily_ci__recommendations__more_information_vulnerable_population",
            provincial_link=provincial_link,
        )
    else:
        dispatcher.utter_message(
            template="utter_daily_ci__recommendations__more_information_general",
            provincial_link=provincial_link,
        )

    if tracker.get_slot(PROVINCE_SLOT) in PROVINCES_WITH_211:
        if tracker.get_slot(PROVINCE_SLOT) == "qc":
            dispatcher.utter_message(template="utter_daily_ci__recommendations__211_qc")
        else:
            dispatcher.utter_message(
                template="utter_daily_ci__recommendations__211_other_provinces"
            )

    dispatcher.utter_message(template="utter_daily_ci__recommendations__tomorrow_ci")

    dispatcher.utter_message(
        template="utter_daily_ci__recommendations__recommendation_1"
    )

    dispatcher.utter_message(
        template="utter_daily_ci__recommendations__recommendation_2"
    )


def _get_provincial__info_link(tracker: Tracker, domain: Dict[Text, Any]) -> str:
    province = tracker.get_slot(PROVINCE_SLOT)
    response = domain.get("responses", {}).get(
        f"provincial_info_link_{province}", [{"text": DEFAULT_INFO_LINK}]
    )
    return response[0].get("text", DEFAULT_INFO_LINK)
