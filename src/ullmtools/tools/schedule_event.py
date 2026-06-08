def create_schedule_event_tool(
    scheduler
):

    def schedule_event(
        delay_seconds,
        tool_name,
        arguments=None
    ):

        scheduler.schedule_tool(
            tool_name,
            delay_seconds,
            arguments
        )

        return (
            "Evento agendado."
        )

    return schedule_event