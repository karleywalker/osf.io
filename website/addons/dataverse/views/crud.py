import os
import datetime

from framework import request, make_response
from framework.flask import secure_filename, redirect
from framework.exceptions import HTTPError

from website.project.decorators import must_be_contributor_or_public, must_have_addon, must_not_be_registration
from website.project.views.node import _view_project
from website.util import rubeus
from website.addons.dataverse.config import HOST

import httplib as http


@must_be_contributor_or_public
@must_have_addon('dataverse', 'node')
def dataverse_download_file(**kwargs):

    file_id = kwargs.get('path')
    if file_id is None:
        raise HTTPError(http.NOT_FOUND)

    return redirect('http://' + HOST + '/dvn/FileDownload/?fileId=' + file_id)

# TODO: Remove unnecessary API calls
@must_be_contributor_or_public
@must_have_addon('dataverse', 'node')
def dataverse_view_file(**kwargs):

    auth = kwargs['auth']
    node = kwargs['node'] or kwargs['project']
    node_settings = kwargs['node_addon']

    file_id = kwargs.get('path')
    if file_id is None:
        raise HTTPError(http.NOT_FOUND)

    connection = node_settings.user_settings.connect(
        node_settings.dataverse_username,
        node_settings.dataverse_password
    )

    study = connection.get_dataverses()[int(node_settings.dataverse_number)].get_study_by_hdl(node_settings.study_hdl)
    file = study.get_file_by_id(file_id)

    # Get file URL
    url = os.path.join(node.api_url, 'dataverse', 'file', file_id)

    # TODO: Render file

    # # Get or create rendered file
    # cache_file = get_cache_file(
    #     file_id, current_sha,
    # )
    # rendered = get_cache_content(node_settings, cache_file)
    # if rendered is None:
    #     _, data, size = connection.file(
    #         node_settings.user, node_settings.repo, file_id, ref=sha,
    #     )
    #     # Skip if too large to be rendered.
    #     if dataverse_settings.MAX_RENDER_SIZE is not None and size > dataverse_settings.MAX_RENDER_SIZE:
    #         rendered = 'File too large to render; download file to view it'
    #     else:
    #         rendered = get_cache_content(
    #             node_settings, cache_file, start_render=True,
    #             file_path=file_name, file_content=data, download_path=url,
    #         )
    rendered = 'File rendering not yet implemented.'

    rv = {
        'file_name': file.name,
        'render_url': url + '/render/',
        'rendered': rendered,
        'download_url': url + '/download/',
    }
    rv.update(_view_project(node, auth))
    return rv



@must_be_contributor_or_public
@must_not_be_registration
@must_have_addon('dataverse', 'node')
def dataverse_upload_file(**kwargs):

    node = kwargs['node'] or kwargs['project']
    auth = kwargs['auth']
    node_settings = kwargs['node_addon']
    now = datetime.datetime.utcnow()

    path = kwargs.get('path', '')

    connection = node_settings.user_settings.connect(
        node_settings.dataverse_username,
        node_settings.dataverse_password
    )
    study = connection.get_dataverses()[int(node_settings.dataverse_number)].get_study_by_hdl(node_settings.study_hdl)

    upload = request.files.get('file')
    filename = secure_filename(upload.filename)
    content = upload.read()

    study.add_file_obj(filename, content, zip=True)
    file_id = study.get_file(filename).fileId

    if file_id is not None:
        # TODO: Log for dataverse
        # node.add_log(
        #     action=(
        #         'dataverse_' + (
        #             models.NodeLog.FILE_ADDED
        #         )
        #     ),
        #     params={
        #         'project': node.parent_id,
        #         'node': node._primary_key,
        #         'path': os.path.join(path, filename),
        #     },
        #     auth=auth,
        #     log_date=now,
        # )

        info = {
            'addon': 'dataverse',
            'name': filename,
            'size': [
                len(content),
                rubeus.format_filesize(len(content))
            ],
            'kind': 'file',
            'urls': {
                    'view': node_settings.owner.api_url + 'dataverse/file/' + file_id + '/',
                    'download': node_settings.owner.api_url + 'dataverse/file/' + file_id + '/download/',
                    'delete': node_settings.owner.api_url + 'dataverse/file/' + file_id + '/',
            },
            'permissions': {
                'view': True,
                'edit': True,
            },
        }

        return info, 201

    raise HTTPError(http.BAD_REQUEST)


@must_be_contributor_or_public
@must_not_be_registration
@must_have_addon('dataverse', 'node')
def dataverse_delete_file(**kwargs):

    node = kwargs['node'] or kwargs['project']
    auth = kwargs['auth']
    node_settings = kwargs['node_addon']

    now = datetime.datetime.utcnow()

    file_id = kwargs.get('path')
    if file_id is None:
        raise HTTPError(http.NOT_FOUND)

    connection = node_settings.user_settings.connect(
        node_settings.dataverse_username,
        node_settings.dataverse_password
    )
    study = connection.get_dataverses()[int(node_settings.dataverse_number)].get_study_by_hdl(node_settings.study_hdl)

    study.delete_file(study.get_file_by_id(file_id))

    # TODO: Logs

    # if data is None:
    #     raise HTTPError(http.BAD_REQUEST)
    #
    # node.add_log(
    #     action='dataverse_' + models.NodeLog.FILE_REMOVED,
    #     params={
    #         'project': node.parent_id,
    #         'node': node._primary_key,
    #         'path': path,
    #         'dataverse': {
    #             'user': node_settings.user,
    #             'repo': node_settings.repo,
    #         },
    #     },
    #     auth=auth,
    #     log_date=now,
    # )

    return {}