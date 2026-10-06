import { api } from "../api.js";
import { h, clear, spinner, emptyState, timeAgo, formatDate, toast } from "../ui.js";
import { navigate } from "../app.js";

const EVENT_LABEL = {
  COMPLAINT_SUBMITTED: "Submitted",
  COMPLAINT_ASSIGNED: "Assigned",
  STATUS_CHANGED: "Status",
  SLA_APPROACHING: "Due soon",
  COMPLAINT_ESCALATED: "Escalated",
  COMPLAINT_RESOLVED: "Resolved",
  COMPLAINT_CLOSED: "Closed",
};

const EVENT_CLASS = {
  SLA_APPROACHING: "s-IN_PROGRESS",
  COMPLAINT_ESCALATED: "s-ESCALATED",
  COMPLAINT_ASSIGNED: "s-ASSIGNED",
};

export async function notificationsView(root) {
  const unreadOnly = h("input", { type: "checkbox", id: "unread-only" });
  const eventType = h(
    "select",
    {
      class: "input",
      id: "event-type",
      "aria-label": "Filter by event type",
    },
    h("option", { value: "" }, "All event types"),
    ...Object.entries(EVENT_LABEL).map(([value, label]) =>
      h("option", { value }, label),
    ),
  );
  const body = h("div", {});

  root.append(
    h(
      "div",
      { class: "page-head" },
      h(
        "div",
        {},
        h("h1", {}, "Notifications"),
        h("p", {}, "Updates on complaints you raised or handle."),
      ),
      h(
        "button",
        {
          class: "btn btn-secondary",
          onclick: async () => {
            const r = await api.markAllRead();
            toast(`${r.updated} marked as read`);
            load();
          },
        },
        "Mark all as read",
      ),
    ),
    h(
      "section",
      { class: "card" },
      h(
        "div",
        { class: "filters" },
        h(
          "label",
          { class: "switch", for: "unread-only" },
          unreadOnly,
          "Unread only",
        ),
        eventType,
      ),
      body,
    ),
  );

  unreadOnly.addEventListener("change", load);
  eventType.addEventListener("change", load);

  async function load() {
    clear(body).append(spinner());

    const data = await api.notifications({
      unread_only: unreadOnly.checked,
      event_type: eventType.value || undefined,
      limit: 100,
    });

    clear(body);

    if (!data.items.length) {
      return body.append(
        emptyState("Nothing here", "You're all caught up."),
      );
    }

    body.append(
      h(
        "div",
        { role: "list" },
        data.items.map((n) =>
          h(
            "div",
            {
              role: "listitem",
              class: `notif${n.read_status ? "" : " unread"}`,
              tabindex: "0",
              onclick: async () => {
                if (!n.read_status) {
                  await api.markRead(n.notification_id).catch(() => {});
                }
                if (n.complaint_id) {
                  navigate(`#/complaints/${n.complaint_id}`);
                } else {
                  load();
                }
              },
            },
            h(
              "div",
              { class: "row-between" },
              h("span", {}, n.message),
              h(
                "span",
                {
                  class: `badge plain ${EVENT_CLASS[n.event_type] || ""}`,
                },
                EVENT_LABEL[n.event_type] || n.event_type,
              ),
            ),
            h(
              "div",
              {
                class: "when",
                title: formatDate(n.created_at),
              },
              timeAgo(n.created_at),
            ),
          ),
        ),
      ),
    );
  }

  await load();
}