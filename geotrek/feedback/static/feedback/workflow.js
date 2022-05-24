$(window).on('entity:view:add entity:view:update', function (e, data) {
    $('#div_id_message_sentinel').prop('hidden', true);
    $('#div_id_message_sentinel_predefined').prop('hidden', true);
    $('#div_id_message_supervisor').prop('hidden', true);
    $('#div_id_uses_timers').prop('hidden', true);
    $('#id_status').change(function () {
        display_message_fields_on_status_change();
    });
    $('#id_assigned_user').change(function () {
        display_message_fields_on_supervisor_change();
    });
    $('#div_id_message_sentinel_predefined').change(function () {
        display_predefined_email_in_email_field();
    });
    return;
});

function display_message_fields_on_status_change() {
    var status_ids_and_colors = JSON.parse($('#status_ids_and_colors').text());
    var selected = $('#id_status').val() || null;
    do_display = ((status_ids_and_colors[selected]['id'] == "solved") || (status_ids_and_colors[selected]['id'] == "classified"))
    $('#div_id_message_sentinel').prop('hidden', !do_display);
    $('#div_id_message_sentinel_predefined').prop('hidden', !do_display);
    // Prevent assigning and classifying at the same time
    if (status_ids_and_colors[selected]['id'] == "classified") {
        $('#id_assigned_user').val("");
        $('#div_id_assigned_user').prop('hidden', true);
        $('#div_id_message_supervisor').prop('hidden', true);
        $('#div_id_uses_timers').prop('hidden', true);
    }
    if (status_ids_and_colors[selected]['id'] == "filed") {
        $('#id_assigned_user').val("");
        $('#div_id_assigned_user').prop('hidden', false);
    }
}

function display_message_fields_on_supervisor_change() {
    var selected = $('#id_assigned_user').val() || null;
    $('#div_id_message_sentinel').prop('hidden', (selected == null));
    $('#div_id_message_sentinel_predefined').prop('hidden', (selected == null));
    $('#div_id_message_supervisor').prop('hidden', (selected == null));
    $('#div_id_uses_timers').prop('hidden', (selected == null));
    $('#div_id_status').prop('hidden', (selected != null));
}

function display_predefined_email_in_email_field() {
    var predefined_emails = JSON.parse($('#predefined_emails').text());
    var resolved_intervention_info = JSON.parse($('#resolved_intervention_info').text());
    var selected = $('#id_message_sentinel_predefined').val() || null;
    if (selected == null) {
        $('#id_message_supervisor').val("");
        $('#id_message_sentinel').val("");
    } else {
        text = predefined_emails[selected]["text"];
        text = text.replace(/##supervisor##/g, resolved_intervention_info["username"]);
        text = text.replace(/##intervention_date##/g, resolved_intervention_info["date"]);
        $('#id_message_supervisor').val(text);
        $('#id_message_sentinel').val(text);
    }
}
