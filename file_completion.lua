require 'mp'
require 'mp.msg'

function print_completion()
    mp.msg.info('percent ' .. mp.get_property('percent-pos'))
end

function file_started()
    mp.msg.info('started ' .. mp.get_property('filename'))
    timer = mp.add_periodic_timer(10, print_completion)
end
mp.register_event('start-file', file_started)

function file_ended()
    mp.msg.info('ended')
    timer:kill()
end
mp.register_event('end-file', file_ended)

function paused()
    timer:stop()
end
mp.register_event('pause', paused)

function unpaused()
    timer:resume()
end
mp.register_event('unpause', unpaused)
