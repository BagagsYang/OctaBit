using Midi8BitSynthesiser.Tests.TestData;

namespace Midi8BitSynthesiser.Tests;

public sealed class RepoRootLocatorTests
{
    [Fact]
    public void BuildMetadata_ResolvesRepoAndSharedPaths()
    {
        var repoRoot = RepoRootLocator.FindRepoRoot();
        var sharedRoot = RepoRootLocator.FindSharedRoot();
        var sharedScriptPath = RepoRootLocator.FindSharedScriptPath();

        Assert.True(Directory.Exists(repoRoot));
        Assert.True(Directory.Exists(sharedRoot));
        Assert.True(File.Exists(sharedScriptPath));
    }
}
