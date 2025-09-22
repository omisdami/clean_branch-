import autogen

def get_user_proxy_agent(llm_config):
    return autogen.UserProxyAgent(
        name="user_proxy",
        human_input_mode="NEVER",
        max_consecutive_auto_reply=5,
        is_termination_msg=lambda x: x.get("content", "").rstrip().endswith("TERMINATE"),
        code_execution_config={
            "work_dir": "web",
            "use_docker": False
        },
        llm_config=llm_config,
        system_message="Reply TERMINATE if the relevant information has been fully extracted. Otherwise, reply CONTINUE."
    )