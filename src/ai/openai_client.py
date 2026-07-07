from openai import OpenAI

client = OpenAI()

def summarize_nasa_events(events):
    """
    AI-assisted summarization of NASA event data.
    Used for Gartner AI AppSec demonstration.
    """

    response = client.responses.create(
        model="gpt-4",
        input=f"Summarize these NASA events:\n{events}"
    )

    return response.output_text


if __name__ == "__main__":
    sample_data = """
    Mars rover detected unusual terrain.
    Near Earth asteroid passed safely.
    ISS crew completed maintenance.
    """

    print(summarize_nasa_events(sample_data))
