import Foundation

public struct TeamEvent: Sendable, Codable {
    public let kind: String
    public let payload: [String: String]

    static func decode(_ line: String) -> TeamEvent? {
        guard let data = line.data(using: .utf8) else { return nil }
        return try? JSONDecoder().decode(TeamEvent.self, from: data)
    }
}

public struct RollcallEntry: Sendable, Codable {
    public let role: String
    public let status: String
    public let latencyMS: Int?

    static func decode(_ line: String) -> RollcallEntry? {
        guard let data = line.data(using: .utf8) else { return nil }
        return try? JSONDecoder().decode(RollcallEntry.self, from: data)
    }
}
