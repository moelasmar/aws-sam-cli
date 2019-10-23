"""
CLI command for "logs" command
"""

import logging
import click

from samcli.cli.main import pass_context, common_options as cli_framework_options, aws_creds_options
from samcli.lib.telemetry.metrics import track_command

LOG = logging.getLogger(__name__)

HELP_TEXT = """
Use this command to fetch logs generated by your Lambda function.\n
\b
When your functions are a part of a CloudFormation stack, you can fetch logs using the function's
LogicalID when you specify the stack name.
$ sam logs -n HelloWorldFunction --stack-name mystack \n
\b
Or, you can fetch logs using the function's name.
$ sam logs -n mystack-HelloWorldFunction-1FJ8PD36GML2Q \n
\b
You can view logs for a specific time range using the -s (--start-time) and -e (--end-time) options
$ sam logs -n HelloWorldFunction --stack-name mystack -s '10min ago' -e '2min ago' \n
\b
You can also add the --tail option to wait for new logs and see them as they arrive.
$ sam logs -n HelloWorldFunction --stack-name mystack --tail \n
\b
Use the --filter option to quickly find logs that match terms, phrases or values in your log events.
$ sam logs -n HelloWorldFunction --stack-name mystack --filter "error" \n
"""


@click.command("logs", help=HELP_TEXT, short_help="Fetch logs for a function")
@click.option(
    "--name",
    "-n",
    required=True,
    help="Name of your AWS Lambda function. If this function is a part of a CloudFormation stack, "
    "this can be the LogicalID of function resource in the CloudFormation/SAM template.",
)
@click.option("--stack-name", default=None, help="Name of the AWS CloudFormation stack that the function is a part of.")
@click.option(
    "--filter",
    default=None,
    help="You can specify an expression to quickly find logs that match terms, phrases or values in "
    'your log events. This could be a simple keyword (e.g. "error") or a pattern '
    "supported by AWS CloudWatch Logs. See the AWS CloudWatch Logs documentation for the syntax "
    "https://docs.aws.amazon.com/AmazonCloudWatch/latest/logs/FilterAndPatternSyntax.html",
)
@click.option(
    "--start-time",
    "-s",
    default="10m ago",
    help="Fetch logs starting at this time. Time can be relative values like '5mins ago', 'yesterday' or "
    "formatted timestamp like '2018-01-01 10:10:10'. Defaults to '10mins ago'.",
)
@click.option(
    "--end-time",
    "-e",
    default=None,
    help="Fetch logs up to this time. Time can be relative values like '5mins ago', 'tomorrow' or "
    "formatted timestamp like '2018-01-01 10:10:10'",
)
@click.option(
    "--tail",
    "-t",
    is_flag=True,
    help="Tail the log output. This will ignore the end time argument and continue to fetch logs as they "
    "become available.",
)
@cli_framework_options
@aws_creds_options
@pass_context
@track_command
def cli(ctx, name, stack_name, filter, tail, start_time, end_time):  # pylint: disable=redefined-builtin
    # All logic must be implemented in the ``do_cli`` method. This helps with easy unit testing

    do_cli(name, stack_name, filter, tail, start_time, end_time)  # pragma: no cover


def do_cli(function_name, stack_name, filter_pattern, tailing, start_time, end_time):
    """
    Implementation of the ``cli`` method
    """
    from .logs_context import LogsCommandContext

    LOG.debug("'logs' command is called")

    with LogsCommandContext(
        function_name,
        stack_name=stack_name,
        filter_pattern=filter_pattern,
        start_time=start_time,
        end_time=end_time,
        # output_file is not yet supported by CLI
        output_file=None,
    ) as context:

        if tailing:
            events_iterable = context.fetcher.tail(
                context.log_group_name, filter_pattern=context.filter_pattern, start=context.start_time
            )
        else:
            events_iterable = context.fetcher.fetch(
                context.log_group_name,
                filter_pattern=context.filter_pattern,
                start=context.start_time,
                end=context.end_time,
            )

        formatted_events = context.formatter.do_format(events_iterable)

        for event in formatted_events:
            # New line is not necessary. It is already in the log events sent by CloudWatch
            click.echo(event, nl=False)
