# -*- coding: utf-8 -*-

import asyncio
import aiohttp
import tqdm


def async_req(list_request, headers=None, auth=None, decode=False, schedule=0, request_type='GET'):

    async def _manage(_list, _auth, _sched):
        _tasks = []

        #Single request
        async def _single_request(_request,_sched):
            await asyncio.sleep(_sched)
            async with session.request(request_type, _request) as resp:
                assert resp.status == 200
                return await resp.read()

        #Creating all asyncio tasks
        if(_auth != None):
            _b_auth = aiohttp.BasicAuth(_auth['login'], password=_auth['password'])
        else:
            _b_auth = None
        async with aiohttp.ClientSession(loop=asyncio.get_event_loop(), auth=_b_auth, headers=headers) as session:
            _delay = 0
            for _req in _list:
                task = asyncio.create_task(_single_request(_req, _delay))
                _tasks.append(task)
                _delay = _delay + _sched
            for f in tqdm.tqdm(asyncio.as_completed(_tasks), total=len(_tasks), ncols=100 ):
                await f
        return _tasks
    _completed_tasks = asyncio.run(_manage(list_request, auth, schedule))
    if decode:
        _tasks_to_return = [task.result().decode() for task in _completed_tasks]
    else:
        _tasks_to_return = [task.result() for task in _completed_tasks]
    return _tasks_to_return
