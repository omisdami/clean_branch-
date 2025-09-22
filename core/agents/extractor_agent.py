import autogen

def get_extractor_agent(llm_config):
    return autogen.AssistantAgent(
        name="extractor_agent",
        llm_config=llm_config,
        system_message="""
            You are a skilled **Document Extractor Agent**.

            Your task is to analyze the full document content and extract **structured, factual information** organized by predefined section titles.

            Instructions:
            - For each section title provided, extract **relevant facts only** from the document.
            - Use dictionary format like: 
              {
                "Section Title": {
                    "Company Name": "Value",
                    "Key Fact": "Value",
                    ...
                },
                ...
              }
            - Always include a Company Name key and value in every section for future reference.
            - If a section has no relevant information, return an empty object for that section.
            - Do NOT summarize or interpret — only extract direct facts and values.

            End your response with the word: TERMINATE
        """
    )
