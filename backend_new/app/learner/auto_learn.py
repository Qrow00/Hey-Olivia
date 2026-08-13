"""MistakeLearner - turns mistakes in the conversation stream into lessons.

Non-intrusive auto-learning that works WITHOUT the user calling /teach:

  - correction cues after a reply ("no, I meant X", "that's wrong", a rephrase)
    -> the previous utterance is re-taught with the corrected intent
  - skill executions that fail -> recorded as bad feedback
  - low-confidence classifier parses -> recorded for review

Every correction is applied LIVE to the running classifier (and persisted)
AND recorded as feedback so the background retrain job replays it later.
"""

import re
from typing import Any, Dict, Optional

CORRECTION_PATTERNS = [
    re.compile(r"^\s*(no|nope|wrong|incorrect|not that|nah)\b", re.I),
    re.compile(r"\b(that'?s|that is|you (got|made) it)\s+(not|wrong)\b", re.I),
    re.compile(r"\b(you )?(misunderstood|missed|didn'?t (get|understand|hear))\b", re.I),
    re.compile(r"\b(not what i|that's not what i)\s+(meant|asked|said|wanted)\b", re.I),
    re.compile(r"\bi (meant|said|asked for|wanted)\b", re.I),
    re.compile(r"\b(i was )?talking about\b", re.I),
]

INTENT_CUE = re.compile(
    r"\b(?:i (?:meant|said|asked (?:for|about)|wanted)|"
    r"it should (?:be|do|say|play|turn)|"
    r"you should (?:have )?(?:done|said|played|turned))\s+(.+)",
    re.I,
)


class MistakeLearner:
    """Watch the command stream; teach the classifier from detected mistakes."""

    def __init__(self, fb_store: Any, nlu: Any, cfg: Any,
                 confidence_threshold: float = 0.25):
        self.fb = fb_store
        self.nlu = nlu
        self.cfg = cfg
        self.confidence_threshold = confidence_threshold
        self._prev_user: Optional[str] = None
        self._prev_intent: Optional[str] = None
        self._prev_confidence = 0.0
        self._prev_was_skill = False

    async def note(self, user_text: str, result: Dict[str, Any]) -> None:
        """Inspect a completed exchange and learn from any mistake in it."""
        intent = result.get("intent", "chat")
        confidence = float(result.get("confidence", 0.0))
        is_skill = result.get("command_type") == "skill"
        source = result.get("source")

        if self._match_cue(user_text) and self._prev_user is not None:
            await self._correct_previous(user_text)
        elif is_skill and result.get("success") is not True:
            await self._record("bad", note=f"auto: skill '{intent}' failed",
                               text=user_text, intent=intent)
        elif (source == "classifier" and intent != "chat"
              and confidence < self.confidence_threshold):
            await self._record("bad",
                               note=f"auto: low confidence ({confidence:.2f})",
                               text=user_text, intent=intent)

        self._prev_user = user_text
        self._prev_intent = intent
        self._prev_confidence = confidence
        self._prev_was_skill = is_skill

    # --- internals ----------------------------------------------------------

    def _match_cue(self, text: str) -> Optional[re.Pattern]:
        for pat in CORRECTION_PATTERNS:
            if pat.search(text):
                return pat
        return None

    async def _correct_previous(self, current_text: str) -> None:
        """The user is correcting the last reply; re-teach the last command."""
        if self._prev_user is None:
            return
        m = INTENT_CUE.search(current_text)
        corrected = None
        if m:
            parsed = await self.nlu.process(m.group(1).strip())
            corrected = parsed.get("intent")
        if corrected is None or corrected == "chat":
            await self._record("bad", note="auto: correction cue (no rephrase)")
            return
        if corrected != self._prev_intent:
            await self.nlu.teach(self._prev_user, corrected)
        await self._record(
            "bad",
            note=f"auto: corrected '{self._prev_intent}' -> '{corrected}'",
            correction=corrected,
        )

    async def _record(self, rating: str, note: str,
                      text: Optional[str] = None, intent: Optional[str] = None,
                      correction: str = "") -> None:
        text = text or self._prev_user
        intent = intent or self._prev_intent or "chat"
        if self.fb is None or not text:
            return
        try:
            await self.fb.record(text, intent, rating, note=note, correction=correction)
            print(f"[Learner] {note} ('{text}')")
        except Exception as e:
            print(f"[Learner] record error: {e}")
