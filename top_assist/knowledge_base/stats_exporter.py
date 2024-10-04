import logging

import top_assist.database.pages as db_pages
import top_assist.database.spaces as db_spaces
from top_assist.configuration import confluence_stats_page_id, confluence_stats_page_title
from top_assist.confluence.pages import update_page as update_page_in_confluence
from top_assist.knowledge_base.importer import update_space as update_space_in_db
from top_assist.utils.sentry_notifier import sentry_notify_exception


def export_spaces_stats() -> None:
    try:
        page_context = __prepare_page_context()
        response = update_page_in_confluence(
            page_id=confluence_stats_page_id,
            title=confluence_stats_page_title,
            content=page_context,
            minor_edit=True,
        )

        space = db_spaces.find_or_create(space_key=response["space"]["key"], space_name=response["space"]["name"])
        update_space_in_db(space)
    except Exception as e:
        logging.exception("Failed to export spaces stats")
        sentry_notify_exception(e)


def __prepare_page_context() -> str:
    spaces_info = __collect_spaces_data()
    html_table = __generate_html_table(spaces_info)

    context = (
        "The 'Top Assist - Spaces' document provides a comprehensive overview"
        " of the various knowledge base spaces available through Top Assist.\n"
        f"{html_table}"
        "\n\nThis document contains the pages to which Top Assist has access to.\n"
        "New data sources will be added to the knowledge base in the future."
    )
    return context


def __collect_spaces_data() -> list[dict]:
    stats = []
    spaces = db_spaces.all_spaces()
    if not spaces:
        logging.error("No spaces found in the database")
        return []

    for space in spaces:
        pages_count = db_pages.count_all_by_space(space)
        space_stats = {
            "space_key": space.key,
            "space_name": space.name,
            "pages_count": pages_count,
        }
        stats.append(space_stats)
    return stats


def __generate_html_table(spaces: list[dict]) -> str:
    table = """
    <table data-table-width="760" data-layout="default">
        <colgroup>
            <col style="width: 126.0px;" />
            <col style="width: 463.0px;" />
            <col style="width: 164.0px;" />
        </colgroup>
        <tbody>
            <tr>
                <th><p style="text-align: center;"><strong>Space Key</strong></p></th>
                <th><p style="text-align: center;"><strong>Space Name</strong></p></th>
                <th><p style="text-align: center;"><strong>Number of Pages</strong></p></th>
            </tr>
    """
    for space in spaces:
        table += f"""
            <tr>
                <td><p style="text-align: center;">{space["space_key"]}</p></td>
                <td><p style="text-align: center;">{space["space_name"]}</p></td>
                <td><p style="text-align: center;">{space["pages_count"]}</p></td>
            </tr>"""
    table += """
        </tbody>
    </table>
    """
    return table
