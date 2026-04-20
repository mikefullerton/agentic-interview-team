import Foundation

public struct AtpLocator: Sendable {
    public let python: URL
    public let cli: URL

    public static let auto = AtpLocator(python: URL(fileURLWithPath: "/usr/bin/env"), cli: URL(fileURLWithPath: "atp_cli.py"))

    public init(python: URL, cli: URL) {
        self.python = python
        self.cli = cli
    }

    /// Resolves to an absolute path, searching the repo layout if `cli` is unresolved.
    func resolved() throws -> AtpLocator {
        if cli.path.hasPrefix("/") && FileManager.default.fileExists(atPath: cli.path) {
            return self
        }
        // Walk up from CWD looking for skills/atp/scripts/atp_cli.py
        var dir = URL(fileURLWithPath: FileManager.default.currentDirectoryPath)
        for _ in 0..<8 {
            let candidate = dir.appendingPathComponent("skills/atp/scripts/atp_cli.py")
            if FileManager.default.fileExists(atPath: candidate.path) {
                return AtpLocator(python: resolvePython3(), cli: candidate)
            }
            dir.deleteLastPathComponent()
        }
        throw TeamError.atpNotFound
    }
}

private func resolvePython3() -> URL {
    let candidates = ["/usr/bin/python3", "/opt/homebrew/bin/python3", "/usr/local/bin/python3"]
    for path in candidates where FileManager.default.fileExists(atPath: path) {
        return URL(fileURLWithPath: path)
    }
    return URL(fileURLWithPath: "/usr/bin/env")
}
