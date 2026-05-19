import EventKit
import Foundation

struct LaunchEvent: Decodable {
    let title: String
    let category: String
    let start: String
    let end: String
    let allDay: Bool
    let location: String?
    let url: String?
    let source: String?
    let summary: String?
    let score: Int?
    let matchedDate: String?

    enum CodingKeys: String, CodingKey {
        case title
        case category
        case start
        case end
        case allDay = "all_day"
        case location
        case url
        case source
        case summary
        case score
        case matchedDate = "matched_date"
    }
}

struct Arguments {
    var eventsPath = "out/events.json"
    var statePath = "out/mac_calendar_state.json"
    var calendarName = "科技新品发布会日程"
    var authorizeOnly = false
    var dryRun = false
}

enum SyncError: Error, CustomStringConvertible {
    case message(String)

    var description: String {
        switch self {
        case .message(let value):
            return value
        }
    }
}

func parseArguments() -> Arguments {
    var args = Arguments()
    var index = 1
    let argv = CommandLine.arguments
    while index < argv.count {
        let arg = argv[index]
        switch arg {
        case "--events":
            index += 1
            if index < argv.count { args.eventsPath = argv[index] }
        case "--state":
            index += 1
            if index < argv.count { args.statePath = argv[index] }
        case "--calendar-name":
            index += 1
            if index < argv.count { args.calendarName = argv[index] }
        case "--authorize-only":
            args.authorizeOnly = true
        case "--dry-run":
            args.dryRun = true
        default:
            break
        }
        index += 1
    }
    return args
}

func requestCalendarAccess(store: EKEventStore) throws {
    let status = EKEventStore.authorizationStatus(for: .event)

    // rawValue 3 is full calendar access on current macOS and authorized on older macOS.
    if status.rawValue == 3 {
        return
    }

    if status != .notDetermined {
        throw SyncError.message("Mac 日历权限未开启。请到 系统设置 -> 隐私与安全性 -> 日历 里允许终端或 Codex 访问。")
    }

    let semaphore = DispatchSemaphore(value: 0)
    var granted = false
    var requestError: Error?

    if #available(macOS 14.0, *) {
        store.requestFullAccessToEvents { ok, error in
            granted = ok
            requestError = error
            semaphore.signal()
        }
    } else {
        store.requestAccess(to: .event) { ok, error in
            granted = ok
            requestError = error
            semaphore.signal()
        }
    }

    semaphore.wait()

    if let requestError {
        throw requestError
    }
    if !granted {
        throw SyncError.message("未获得 Mac 日历权限。")
    }
}

func loadEvents(path: String) throws -> [LaunchEvent] {
    let url = URL(fileURLWithPath: path)
    guard FileManager.default.fileExists(atPath: url.path) else {
        return []
    }
    let data = try Data(contentsOf: url)
    return try JSONDecoder().decode([LaunchEvent].self, from: data)
}

func loadState(path: String) -> [String: String] {
    let url = URL(fileURLWithPath: path)
    guard
        FileManager.default.fileExists(atPath: url.path),
        let data = try? Data(contentsOf: url),
        let state = try? JSONDecoder().decode([String: String].self, from: data)
    else {
        return [:]
    }
    return state
}

func saveState(_ state: [String: String], path: String) throws {
    let url = URL(fileURLWithPath: path)
    try FileManager.default.createDirectory(at: url.deletingLastPathComponent(), withIntermediateDirectories: true)
    let data = try JSONEncoder().encode(state)
    try data.write(to: url, options: .atomic)
}

func parseDate(_ value: String) throws -> Date {
    let iso = ISO8601DateFormatter()
    iso.formatOptions = [.withInternetDateTime, .withFractionalSeconds]
    if let date = iso.date(from: value) {
        return date
    }
    iso.formatOptions = [.withInternetDateTime]
    if let date = iso.date(from: value) {
        return date
    }
    throw SyncError.message("无法解析时间：\(value)")
}

func ensureCalendar(name: String, store: EKEventStore) throws -> EKCalendar {
    if let existing = store.calendars(for: .event).first(where: { $0.title == name }) {
        return existing
    }

    let calendar = EKCalendar(for: .event, eventStore: store)
    calendar.title = name

    if let defaultSource = store.defaultCalendarForNewEvents?.source {
        calendar.source = defaultSource
    } else if let localSource = store.sources.first(where: { $0.sourceType == .local }) {
        calendar.source = localSource
    } else if let firstSource = store.sources.first {
        calendar.source = firstSource
    } else {
        throw SyncError.message("没有可用的 Mac 日历账户来源。")
    }

    try store.saveCalendar(calendar, commit: true)
    return calendar
}

func categoryLabel(_ value: String) -> String {
    switch value {
    case "mobile": return "手机新品"
    case "ev": return "新能源汽车"
    case "tech": return "科技数码"
    default: return value
    }
}

func stableKey(for event: LaunchEvent) -> String {
    let basis = [
        event.category,
        event.title,
        event.url ?? "",
        String(event.start.prefix(10))
    ].joined(separator: "|")
    return fnv1a64(basis)
}

func fnv1a64(_ value: String) -> String {
    var hash: UInt64 = 14695981039346656037
    for byte in value.utf8 {
        hash ^= UInt64(byte)
        hash = hash &* 1099511628211
    }
    return String(format: "%016llx", hash)
}

func eventNotes(for event: LaunchEvent, key: String) -> String {
    var lines = [
        "launch-calendar-bot-id:\(key)"
    ]
    if let matchedDate = event.matchedDate, !matchedDate.isEmpty {
        lines.append("识别时间：\(matchedDate)")
    }
    if let score = event.score {
        lines.append("可信度分数：\(score)")
    }
    return lines.joined(separator: "\n")
}

func findEventByMarker(store: EKEventStore, calendar: EKCalendar, key: String, around start: Date) -> EKEvent? {
    let from = Calendar.current.date(byAdding: .day, value: -3, to: start) ?? start
    let to = Calendar.current.date(byAdding: .day, value: 3, to: start) ?? start
    let predicate = store.predicateForEvents(withStart: from, end: to, calendars: [calendar])
    return store.events(matching: predicate).first { event in
        event.notes?.contains("launch-calendar-bot-id:\(key)") == true
    }
}

func applyLaunchEvent(_ launch: LaunchEvent, to event: EKEvent, key: String) throws {
    event.title = "[\(categoryLabel(launch.category))] \(launch.title)"
    event.startDate = try parseDate(launch.start)
    event.endDate = try parseDate(launch.end)
    event.isAllDay = launch.allDay
    event.location = launch.location ?? "线上"
    event.notes = eventNotes(for: launch, key: key)
    event.url = nil
}

func sync(args: Arguments) throws {
    let events = try loadEvents(path: args.eventsPath)

    if args.dryRun {
        print("Mac Calendar dry-run: \(events.count) events")
        for event in events {
            print("- \(event.start) \(event.title)")
        }
        return
    }

    if events.isEmpty && !args.authorizeOnly {
        print("Mac Calendar sync skipped: no events in \(args.eventsPath)")
        return
    }

    let store = EKEventStore()
    try requestCalendarAccess(store: store)
    let calendar = try ensureCalendar(name: args.calendarName, store: store)

    if args.authorizeOnly {
        print("Mac 日历授权成功，目标日历：\(calendar.title)")
        return
    }

    var state = loadState(path: args.statePath)
    var created = 0
    var updated = 0

    for launch in events {
        let key = stableKey(for: launch)
        let startDate = try parseDate(launch.start)
        var target: EKEvent?

        if let existingId = state[key] {
            target = store.event(withIdentifier: existingId)
        }
        if target == nil {
            target = findEventByMarker(store: store, calendar: calendar, key: key, around: startDate)
        }

        if let event = target {
            try applyLaunchEvent(launch, to: event, key: key)
            try store.save(event, span: .thisEvent, commit: true)
            state[key] = event.eventIdentifier
            updated += 1
        } else {
            let event = EKEvent(eventStore: store)
            event.calendar = calendar
            try applyLaunchEvent(launch, to: event, key: key)
            try store.save(event, span: .thisEvent, commit: true)
            state[key] = event.eventIdentifier
            created += 1
        }
    }

    try saveState(state, path: args.statePath)
    print("Mac Calendar sync complete: created \(created), updated \(updated), calendar \(calendar.title)")
}

do {
    try sync(args: parseArguments())
} catch {
    fputs("Mac Calendar sync failed: \(error)\n", stderr)
    exit(1)
}
