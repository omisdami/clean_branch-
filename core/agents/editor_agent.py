import autogen

def get_editor_agent(llm_config):
    return autogen.AssistantAgent(
        name="editor_agent",
        llm_config=llm_config,
        system_message="""
        You are a highly capable document revision assistant. Your role is to apply user-specified corrections to an existing document or report.

        - Modify the document content according to the user's request.
        - Preserve all other content unless directly related to the change.
        - Return the **entire updated document as text**, preserving the original structure and formatting.
        - Do not explain your changes — only return the revised document.

        End your response with: TERMINATE
        """
    )
