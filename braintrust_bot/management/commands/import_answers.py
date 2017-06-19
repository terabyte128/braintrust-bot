from django.core.management.base import BaseCommand

from braintrust_bot.models import EightBallAnswer


class Command(BaseCommand):
    def handle(self, *args, **options):


        chat_id = -104306145

        answers = [
            "Without a doubt.",
            "Yes.",
            "Fo shizzle, my dizzle.",
            "No.",
            "Ye.",
            "Nah",
            "Fuck no.",
            "Absolutely.",
            "Definitely.",
            "Definitely not.",
            "No way.",
            "Signs point to yes.",
            "Indubitably.",
            "Most Likely.",
            "Probably not.",
            "Not likely.",
            "Unlikely.",
            "Sure, why not.",
            "My sources say no.",
            "Fuck off.",
            "Fuckin... hell yeah, dude.",
            "Nooooope.",
            "Fuck yeah.",
            "YES.",
            "NO.",
            "HAHAHAHAHA... No.",
            "I think you already know the answer.",
            "Impossible.",
            "YES! Just kidding.",
            "Confirmed.",
            "👍",
            "👎",
            "👌",
            "❌",
            "✅",
            "What a stupid question.",
            "Who cares, let's get high.",
            "Ayup.",
            "Nope.",
            "I think so.",
            "Uh, no.",
            "Probably, yeah.",
            "Oh yeeeaah.",
            "Mmm, you bet.",
            "Not in a million years, dude.",
            "Yes. And by yes, I mean no.",
            "I don't have any info on that, try Googling it.",
            "Leave me alone, I'm hungover.",
            "Ask Caelan to arbit."
        ]

        for line in answers:
            response = EightBallAnswer(answer=line, chat_id=chat_id)
            response.save()
