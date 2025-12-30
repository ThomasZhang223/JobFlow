"use client";

import { useState, useEffect, useRef } from "react";
import { Play, Mail, Clock, MapPin, Briefcase, DollarSign, Search, Filter, X, Bookmark, TrendingUp, AlertCircle, CheckCircle, Target } from "lucide-react";

interface ScrapeUpdate {
  task_id: string;
  status: "pending" | "running" | "completed" | "failed";
  jobs_found: number;
  error_message?: string;
  timestamp?: string;
  source?: string;
}

interface Job {
  id: string;
  title: string;
  company: string;
  location: string;
  salary: string;
  date: string;
  experience: string;
  link: string;
  jobType: string;
  isNew?: boolean;
  isSaved?: boolean;
  matchScore?: number;
}

interface UserPreferences {
  experienceLevel: string;
  jobType: string;
  jobTitle: string;
  location: string;
  salaryRange: [number, number];
  email: string;
  hoursInterval: number;
  sendEmail: boolean;
}

// Default preferences
const DEFAULT_PREFERENCES: UserPreferences = {
  experienceLevel: "Entry Level",
  jobType: "Full-time",
  jobTitle: "Software Engineer",
  location: "Toronto, ON",
  salaryRange: [70000, 120000],
  email: "",
  hoursInterval: 24,
  sendEmail: true,
};

export default function JobFlowScraper() {
  const socketRef = useRef<WebSocket | null>(null);
  const [status, setStatus] = useState<"connecting" | "open" | "closed">("connecting");
  const [updates, setUpdates] = useState<ScrapeUpdate[]>([]);
  const [isScraperRunning, setIsScraperRunning] = useState(false);
  const [isLoggedIn, setIsLoggedIn] = useState(false);
  const [userEmail, setUserEmail] = useState("");
  const [showLoginModal, setShowLoginModal] = useState(false);
  const [loginEmail, setLoginEmail] = useState("");
  const [loginPassword, setLoginPassword] = useState("");
  const [loginError, setLoginError] = useState("");

  // User preferences with localStorage
  const [preferences, setPreferences] = useState<UserPreferences>(DEFAULT_PREFERENCES);
  const [draftPreferences, setDraftPreferences] = useState<UserPreferences>(DEFAULT_PREFERENCES);


  const [emailError, setEmailError] = useState("");
  const [isEditingPreferences, setIsEditingPreferences] = useState(false);

  // Analytics
  const [stats, setStats] = useState({
    totalJobs: 245,
    newToday: 12,
    averageMatch: 78,
    savedJobs: 8,
  });

  // Job history
  const [jobs, setJobs] = useState<Job[]>([
    { id: "1", title: "Frontend Developer", company: "Tech Corp", location: "Toronto, ON", salary: "$70k-90k", date: "2024-12-28 14:30", experience: "Entry Level", link: "https://techcorp.com/jobs/123", jobType: "Full-time", isNew: true, matchScore: 92 },
    { id: "2", title: "Software Engineer", company: "StartupXYZ", location: "Remote", salary: "$80k-100k", date: "2024-12-27 10:15", experience: "Mid Level", link: "https://startupxyz.com/careers/456", jobType: "Full-time", matchScore: 85, isSaved: true },
    { id: "3", title: "Junior Developer", company: "Innovation Labs", location: "Toronto, ON", salary: "$60k-75k", date: "2024-12-26 09:45", experience: "Entry Level", link: "https://innovationlabs.com/jobs/789", jobType: "Contract", matchScore: 71 },
    { id: "4", title: "React Developer", company: "Digital Agency", location: "Toronto, ON", salary: "$75k-95k", date: "2024-12-28 16:20", experience: "Entry Level", link: "https://digitalagency.com/jobs/321", jobType: "Full-time", isNew: true, matchScore: 88 },
  ]);

  const [selectedJob, setSelectedJob] = useState<Job | null>(null);
  const [searchTerm, setSearchTerm] = useState("");
  const [filterVisible, setFilterVisible] = useState(false);

  // Load preferences from localStorage on mount
  useEffect(() => {
    try {
      const savedPreferences = localStorage.getItem('jobflow_preferences');
      if (savedPreferences) {
        const parsed = JSON.parse(savedPreferences);
        setPreferences(parsed);
      }
    } catch (error) {
      console.error('Error loading preferences from localStorage:', error);
    }
  }, []);

  useEffect(() => {
    const socket = new WebSocket("ws://localhost:8000/ws/scrape");
    socketRef.current = socket;

    socket.onopen = () => {
      setStatus("open");
    };

    socket.onmessage = (event) => {
      try {
        const data: ScrapeUpdate = JSON.parse(event.data);
        setUpdates((prev) => [...prev, { ...data, timestamp: new Date().toLocaleTimeString() }]);
      } catch (e) {
        console.error("Failed to parse message:", event.data);
      }
    };

    socket.onclose = () => setStatus("closed");
    socket.onerror = (error) => console.error("WebSocket error:", error);

    return () => socket.close();
  }, []);

  const validateEmail = (email: string) => {
    const regex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    return regex.test(email);
  };

  const handleEmailChange = (email: string) => {
    setPreferences({ ...preferences, email });
    if (email && !validateEmail(email)) {
      setEmailError("Invalid email format");
    } else {
      setEmailError("");
    }
  };

  const handleSalaryChange = (index: number, value: number) => {
    const newRange: [number, number] = [...preferences.salaryRange] as [number, number];
    newRange[index] = value;

    // Ensure min doesn't exceed max and vice versa
    if (index === 0 && value > newRange[1]) {
      newRange[1] = value;
    } else if (index === 1 && value < newRange[0]) {
      newRange[0] = value;
    }

    setPreferences({ ...preferences, salaryRange: newRange });
  };

  const formatSalary = (value: number) => {
    return `${(value / 1000).toFixed(0)}k`;
  };

  // Save preferences to localStorage
  const handleSavePreferences = () => {
    // Validate email if provided
    if (preferences.email && !validateEmail(preferences.email)) {
      setEmailError("Please enter a valid email address");
      return;
    }

    // Validate salary range
    if (preferences.salaryRange[0] < 0 || preferences.salaryRange[1] < 0) {
      alert("Salary values must be positive");
      return;
    }

    if (preferences.salaryRange[0] > preferences.salaryRange[1]) {
      alert("Minimum salary cannot exceed maximum salary");
      return;
    }

    // Validate hours interval
    if (preferences.hoursInterval < 1 || preferences.hoursInterval > 168) {
      alert("Hours interval must be between 1 and 168 hours");
      return;
    }

    try {
      // Save to localStorage
      localStorage.setItem('jobflow_preferences', JSON.stringify(preferences));

      // Close edit mode
      setIsEditingPreferences(false);
      setEmailError("");
    } catch (error) {
      console.error('Error saving preferences to localStorage:', error);
      alert("Failed to save preferences. Please try again.");
    }
  };

  const handleStartScrape = () => {
    setIsScraperRunning(true);
    // Add logic to trigger scraper
    setTimeout(() => setIsScraperRunning(false), 3000);
  };

  const toggleSaveJob = (jobId: string) => {
    setJobs(jobs.map(job =>
      job.id === jobId ? { ...job, isSaved: !job.isSaved } : job
    ));
  };

  const filteredJobs = jobs.filter(job =>
    job.title.toLowerCase().includes(searchTerm.toLowerCase()) ||
    job.company.toLowerCase().includes(searchTerm.toLowerCase())
  );

  return (
    <div className="min-h-screen bg-white p-6">
      <div className="max-w-7xl mx-auto space-y-6">
        {/* Header */}
        <div className="flex items-center justify-between">
          <h1 className="text-4xl font-bold text-[#2164F3] tracking-tight">JobFlow</h1>

          <div className="flex items-center gap-4">
            {/* Connection Status */}
            <div className="flex items-center gap-2 text-sm">
              <div className={`w-2 h-2 rounded-full ${status === 'open' ? 'bg-green-500' : 'bg-red-500'}`} />
              <span className="text-[#2c2c2c]">
                {status === 'open' ? 'Connected' : 'Disconnected'}
              </span>
            </div>

            {/* Login Section */}
            {!isLoggedIn ? (
              <button
                onClick={() => {
                  setShowLoginModal(true);
                }}
                className="bg-[#2164F3] hover:bg-[#1a4ec7] text-white px-4 py-2 rounded-lg text-sm font-semibold transition-colors"
              >
                Log in
              </button>
            ) : (
              <div className="flex items-center gap-3">
                <span className="text-sm text-[#2164F3] font-medium">
                  {userEmail}
                </span>
                <button
                  onClick={() => {
                    setIsLoggedIn(false);
                    setUserEmail("");
                  }}
                  className="text-sm border-2 border-[#2164F3] text-[#2164F3] px-3 py-1.5 rounded-lg hover:bg-blue-50 transition-colors"
                >
                  Log out
                </button>
              </div>
            )}
          </div>
        </div>


        {/* Start Scrape Button */}
        <div className="relative">
          <div className="absolute -inset-1 bg-gradient-to-r from-[#2164F3] via-[#1a4ec7] to-[#2164F3] rounded-lg blur opacity-75 group-hover:opacity-100 transition duration-1000 animate-pulse"></div>
          <button
            onClick={handleStartScrape}
            disabled={isScraperRunning}
            className="relative w-full bg-gradient-to-r from-[#2164F3] to-[#1a4ec7] hover:from-[#1a4ec7] hover:to-[#2164F3] py-6 rounded-lg font-black text-2xl flex items-center justify-center gap-4 transition-all duration-300 disabled:opacity-50 shadow-2xl transform hover:scale-[1.02] active:scale-[0.98] border-2 border-white/20"
          >
            <Play className="w-8 h-8 fill-white stroke-white" />
            <span className="text-white" style={{ textShadow: '2px 2px 8px rgba(0,0,0,0.9), 0 0 20px rgba(255,255,255,0.3)' }}>
              {isScraperRunning ? "SCRAPING IN PROGRESS..." : "START SCRAPE"}
            </span>
          </button>
        </div>

        {/* Stats Dashboard */}
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
          <div className="bg-white rounded-lg shadow-md border-2 border-[#2164F3] p-4">
            <div className="flex items-center gap-2 mb-2">
              <Briefcase className="w-5 h-5 text-[#2164F3]" />
              <span className="text-sm text-[#2164F3] font-medium">Total Jobs</span>
            </div>
            <p className="text-3xl font-bold text-[#2164F3]">{stats.totalJobs}</p>
          </div>

          <div className="bg-white rounded-lg shadow-md border-2 border-[#2164F3] p-4">
            <div className="flex items-center gap-2 mb-2">
              <TrendingUp className="w-5 h-5 text-[#2164F3]" />
              <span className="text-sm text-[#2164F3] font-medium">New Today</span>
            </div>
            <p className="text-3xl font-bold text-[#2164F3]">{stats.newToday}</p>
          </div>

          <div className="bg-white rounded-lg shadow-md border-2 border-[#2164F3] p-4">
            <div className="flex items-center gap-2 mb-2">
              <Target className="w-5 h-5 text-[#2164F3]" />
              <span className="text-sm text-[#2164F3] font-medium">Avg Match</span>
            </div>
            <p className="text-3xl font-bold text-[#2164F3]">{stats.averageMatch}%</p>
          </div>

          <div className="bg-white rounded-lg shadow-md border-2 border-[#2164F3] p-4">
            <div className="flex items-center gap-2 mb-2">
              <Bookmark className="w-5 h-5 text-[#2164F3]" />
              <span className="text-sm text-[#2164F3] font-medium">Saved Jobs</span>
            </div>
            <p className="text-3xl font-bold text-[#2164F3]">{stats.savedJobs}</p>
          </div>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* User Preferences */}
          <div className="bg-white rounded-lg shadow-md border-2 border-[#2164F3] p-6">
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-xl font-semibold text-[#2164F3]">Preferences</h2>
              {!isEditingPreferences ? (
                <button
                onClick={() => {
                  setDraftPreferences(preferences);
                  setIsEditingPreferences(true);
                }}
                  className="text-sm bg-[#2164F3] hover:bg-[#1a4ec7] text-white px-4 py-2 rounded transition-colors font-medium"
                >
                  Edit
                </button>
              ) : (
                <button
                  onClick={() => {
                    setIsEditingPreferences(false);
                    setEmailError("");
                  }}
                  className="text-sm bg-white hover:bg-gray-50 text-[#2164F3] border-2 border-[#2164F3] px-4 py-2 rounded transition-colors font-medium"
                >
                  Cancel
                </button>
              )}
            </div>

            <div className="space-y-4">
              <div className="flex items-start gap-3">
                <Briefcase className="w-5 h-5 text-[#2164F3] mt-1" />
                <div className="flex-1">
                  <label className="text-sm font-medium text-[#2164F3] block mb-1">Job Title</label>
                  {isEditingPreferences ? (
                    <input
                      type="text"
                      value={draftPreferences.jobTitle}
                      onChange={(e) => setDraftPreferences({ ...draftPreferences, jobTitle: e.target.value })}
                      className="w-full px-3 py-2 border-2 border-[#2164F3] rounded focus:outline-none focus:ring-2 focus:ring-[#2164F3]"
                      placeholder="e.g., Software Engineer"
                    />
                  ) : (
                    <p className="text-[#2164F3]">{draftPreferences.jobTitle}</p>
                  )}
                </div>
              </div>

              <div className="flex items-start gap-3">
                <Briefcase className="w-5 h-5 text-[#2164F3] mt-1" />
                <div className="flex-1">
                  <label className="text-sm font-medium text-[#2164F3] block mb-1">Experience Level</label>
                  {isEditingPreferences ? (
                    <input
                      type="text"
                      value={draftPreferences.experienceLevel}
                      onChange={(e) => setDraftPreferences({ ...draftPreferences, experienceLevel: e.target.value })}
                      className="w-full px-3 py-2 border-2 border-[#2164F3] rounded focus:outline-none focus:ring-2 focus:ring-[#2164F3]"
                    />
                  ) : (
                    <p className="text-[#2164F3]">{draftPreferences.experienceLevel}</p>
                  )}
                </div>
              </div>

              <div className="flex items-start gap-3">
                <Briefcase className="w-5 h-5 text-[#2164F3] mt-1" />
                <div className="flex-1">
                  <label className="text-sm font-medium text-[#2164F3] block mb-1">Job Type</label>
                  {isEditingPreferences ? (
                    <select
                      value={preferences.jobType}
                      onChange={(e) => setPreferences({ ...draftPreferences, jobType: e.target.value })}
                      className="w-full px-3 py-2 border-2 border-[#2164F3] rounded focus:outline-none focus:ring-2 focus:ring-[#2164F3]"
                    >
                      <option value="Full-time">Full-time</option>
                      <option value="Part-time">Part-time</option>
                      <option value="Contract">Contract</option>
                      <option value="Internship">Internship</option>
                    </select>
                  ) : (
                    <p className="text-[#2164F3]">{preferences.jobType}</p>
                  )}
                </div>
              </div>

              <div className="flex items-start gap-3">
                <MapPin className="w-5 h-5 text-[#2164F3] mt-1" />
                <div className="flex-1">
                  <label className="text-sm font-medium text-[#2164F3] block mb-1">Location</label>
                  {isEditingPreferences ? (
                    <input
                      type="text"
                      value={preferences.location}
                      onChange={(e) => setPreferences({ ...preferences, location: e.target.value })}
                      className="w-full px-3 py-2 border-2 border-[#2164F3] rounded focus:outline-none focus:ring-2 focus:ring-[#2164F3]"
                    />
                  ) : (
                    <p className="text-[#2164F3]">{preferences.location}</p>
                  )}
                </div>
              </div>

              <div className="flex items-start gap-3">
                <DollarSign className="w-5 h-5 text-[#2164F3] mt-1" />
                <div className="flex-1">
                  <label className="text-sm font-medium text-[#2164F3] block mb-2">
                    Salary Range: {formatSalary(preferences.salaryRange[0])} - {formatSalary(preferences.salaryRange[1])}
                  </label>
                  {isEditingPreferences ? (
                    <div className="space-y-2">
                      <div className="flex gap-2 items-center">
                        <input
                          type="number"
                          min="50000"
                          max="500000"
                          step="5000"
                          value={draftPreferences.salaryRange[0]}
                          onChange={(e) => handleSalaryChange(0, parseInt(e.target.value))}
                          className="w-24 px-2 py-1 border-2 border-[#2164F3] rounded text-sm focus:outline-none focus:ring-2 focus:ring-[#2164F3]"
                          placeholder="Min"
                        />
                        <span className="text-[#2164F3]">to</span>
                        <input
                          type="number"
                          min="50000"
                          max="500000"
                          step="5000"
                          value={preferences.salaryRange[1]}
                          onChange={(e) => handleSalaryChange(1, parseInt(e.target.value))}
                          className="w-24 px-2 py-1 border-2 border-[#2164F3] rounded text-sm focus:outline-none focus:ring-2 focus:ring-[#2164F3]"
                          placeholder="Max"
                        />
                      </div>
                    </div>
                  ) : (
                    <p className="text-[#2164F3]">
                      ${preferences.salaryRange[0].toLocaleString()} - ${preferences.salaryRange[1].toLocaleString()}
                    </p>
                  )}
                </div>
              </div>

              <div className="flex items-start gap-3">
                <Mail className="w-5 h-5 text-[#2164F3] mt-1" />
                <div className="flex-1">
                  <label className="text-sm font-medium text-[#2164F3] block mb-1">Email</label>
                  {isEditingPreferences ? (
                    <div>
                      <input
                        type="email"
                        value={draftPreferences.email}
                        onChange={(e) => handleEmailChange(e.target.value)}
                        className={`w-full px-3 py-2 border-2 rounded focus:outline-none focus:ring-2 ${emailError ? 'border-red-500 focus:ring-red-500' : 'border-[#2164F3] focus:ring-[#2164F3]'
                          }`}
                        placeholder="you@example.com"
                      />
                      {emailError && <p className="text-red-500 text-xs mt-1">{emailError}</p>}
                    </div>
                  ) : (
                    <p className="text-[#2164F3]">{preferences.email || "Not set"}</p>
                  )}
                </div>
              </div>

              <div className="flex items-start gap-3">
                <Clock className="w-5 h-5 text-[#2164F3] mt-1" />
                <div className="flex-1">
                  <label className="text-sm font-medium text-[#2164F3] block mb-1">Hours Between Scrapes</label>
                  {isEditingPreferences ? (
                    <input
                      type="number"
                      min="1"
                      max="168"
                      value={draftPreferences.hoursInterval}
                      onChange={(e) => setDraftPreferences({ ...draftPreferences, hoursInterval: parseInt(e.target.value) })}
                      className="w-full px-3 py-2 border-2 border-[#2164F3] rounded focus:outline-none focus:ring-2 focus:ring-[#2164F3]"
                    />
                  ) : (
                    <p className="text-[#2164F3]">{draftPreferences.hoursInterval} hours</p>
                  )}
                </div>
              </div>

              {isEditingPreferences && (
                <div className="flex items-center gap-3 pt-2">
                  <label className="flex items-center gap-2 cursor-pointer">
                    <input
                      type="checkbox"
                      checked={draftPreferences.sendEmail}
                      onChange={(e) => setDraftPreferences({ ...draftPreferences, sendEmail: e.target.checked })}
                      className="w-4 h-4 text-[#2164F3] border-2 border-[#2164F3] rounded focus:ring-[#2164F3]"
                    />
                    <span className="text-sm text-[#2164F3]">Send email notifications</span>
                  </label>
                </div>
              )}

              {isEditingPreferences && (
                <button
                  onClick={handleSavePreferences}
                  className="w-full bg-[#2164F3] hover:bg-[#1a4ec7] text-white py-3 rounded transition-colors font-semibold"
                >
                  Save Preferences
                </button>
              )}
            </div>
          </div>

          {/* System Updates */}
          <div className="bg-white rounded-lg shadow-md border-2 border-[#2164F3] p-6">
            <h2 className="text-xl font-semibold text-[#2164F3] mb-4">System Updates</h2>
            <div className="h-80 overflow-y-auto space-y-2 custom-scrollbar">
              {updates.length === 0 ? (
                <p className="text-[#2164F3] text-sm">No updates yet. Start a scrape to see messages.</p>
              ) : (
                updates.slice().reverse().map((update, i) => (
                  <div
                    key={i}
                    className={`p-3 rounded border-l-4 ${update.status === 'completed' ? 'bg-green-50 border-green-500' :
                        update.status === 'failed' ? 'bg-red-50 border-red-500' :
                          update.status === 'running' ? 'bg-blue-50 border-blue-500' :
                            'bg-gray-50 border-gray-500'
                      }`}
                  >
                    <div className="flex justify-between items-start mb-1">
                      <div className="flex items-center gap-2">
                        {update.status === 'completed' && <CheckCircle className="w-4 h-4 text-green-500" />}
                        {update.status === 'failed' && <AlertCircle className="w-4 h-4 text-red-500" />}
                        {update.status === 'running' && <Clock className="w-4 h-4 text-blue-500 animate-spin" />}
                        <span className="font-medium text-sm text-[#2164F3]">{update.status.toUpperCase()}</span>
                      </div>
                      <span className="text-xs text-[#2164F3]">{update.timestamp}</span>
                    </div>
                    <p className="text-sm text-[#2164F3]">Jobs found: {update.jobs_found}</p>
                    {update.source && <p className="text-xs text-[#2164F3] mt-1">Source: {update.source}</p>}
                    {update.error_message && (
                      <p className="text-sm text-red-600 mt-1">{update.error_message}</p>
                    )}
                  </div>
                ))
              )}
            </div>
          </div>
        </div>

        {/* Job Search History */}
        <div className="bg-white rounded-lg shadow-md border-2 border-[#2164F3] p-6">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-xl font-semibold text-[#2164F3]">Job History</h2>
            <div className="flex items-center gap-2">
              <div className="relative">
                <Search className="w-4 h-4 absolute left-3 top-1/2 -translate-y-1/2 text-[#2164F3]" />
                <input
                  type="text"
                  placeholder="Search jobs..."
                  value={searchTerm}
                  onChange={(e) => setSearchTerm(e.target.value)}
                  className="pl-10 pr-4 py-2 border-2 border-[#2164F3] rounded-lg focus:outline-none focus:ring-2 focus:ring-[#2164F3] text-sm"
                />
              </div>
              <button
                onClick={() => setFilterVisible(!filterVisible)}
                className="p-2 border-2 border-[#2164F3] rounded-lg hover:bg-[#2164F3] hover:text-white transition-colors"
              >
                <Filter className="w-4 h-4" />
              </button>
            </div>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {filteredJobs.map((job) => (
              <div
                key={job.id}
                className="relative p-4 border-2 border-[#2164F3] rounded-lg hover:border-[#1a4ec7] hover:shadow-lg transition-all cursor-pointer group bg-white"
              >
                {/* Match Score Badge */}
                {job.matchScore && (
                  <div className={`absolute top-3 right-3 px-2 py-1 rounded text-xs font-bold ${job.matchScore >= 85 ? 'bg-green-100 text-green-700' :
                      job.matchScore >= 70 ? 'bg-blue-100 text-blue-700' :
                        'bg-gray-100 text-gray-700'
                    }`}>
                    {job.matchScore}% Match
                  </div>
                )}

                {/* New Badge */}
                {job.isNew && (
                  <div className="absolute top-3 left-3 bg-[#2164F3] text-white px-2 py-1 rounded text-xs font-bold animate-pulse">
                    NEW
                  </div>
                )}

                <div onClick={() => setSelectedJob(job)} className="pt-6">
                  <h3 className="font-semibold text-[#2164F3] mb-1 pr-16">{job.title}</h3>
                  <p className="text-sm text-[#2164F3] mb-2">{job.company}</p>
                  <div className="space-y-1">
                    <div className="flex items-center gap-2 text-xs text-[#2164F3]">
                      <MapPin className="w-3 h-3" />
                      {job.location}
                    </div>
                    <div className="flex items-center gap-2 text-xs text-[#2164F3]">
                      <DollarSign className="w-3 h-3" />
                      {job.salary}
                    </div>
                    <p className="text-xs text-[#2164F3] mt-2">{job.date}</p>
                  </div>
                </div>

                {/* Save Button */}
                <button
                  onClick={(e) => {
                    e.stopPropagation();
                    toggleSaveJob(job.id);
                  }}
                  className="absolute bottom-3 right-3 p-2 rounded-full hover:bg-blue-50 transition-colors"
                >
                  <Bookmark
                    className={`w-5 h-5 ${job.isSaved ? 'fill-[#2164F3] text-[#2164F3]' : 'text-[#2164F3]'}`}
                  />
                </button>
              </div>
            ))}
          </div>
        </div>

        {/* Job Detail Modal */}
        {selectedJob && (
          <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50" onClick={() => setSelectedJob(null)}>
            <div className="bg-white rounded-lg shadow-xl max-w-2xl w-full p-6" onClick={(e) => e.stopPropagation()}>
              <div className="flex items-start justify-between mb-6">
                <h2 className="text-2xl font-bold text-[#2164F3]">{selectedJob.title}</h2>
                <button
                  onClick={() => setSelectedJob(null)}
                  className="text-[#2164F3] hover:text-[#1a4ec7]"
                >
                  <X className="w-6 h-6" />
                </button>
              </div>

              <div className="space-y-3">
                <div className="flex items-center gap-3">
                  <Briefcase className="w-5 h-5 text-[#2164F3]" />
                  <div>
                    <span className="font-medium text-[#2164F3]">Company: </span>
                    <span className="text-[#2164F3]">{selectedJob.company}</span>
                  </div>
                </div>

                <div className="flex items-center gap-3">
                  <MapPin className="w-5 h-5 text-[#2164F3]" />
                  <div>
                    <span className="font-medium text-[#2164F3]">Location: </span>
                    <span className="text-[#2164F3]">{selectedJob.location}</span>
                  </div>
                </div>

                <div className="flex items-center gap-3">
                  <DollarSign className="w-5 h-5 text-[#2164F3]" />
                  <div>
                    <span className="font-medium text-[#2164F3]">Salary: </span>
                    <span className="text-[#2164F3]">{selectedJob.salary}</span>
                  </div>
                </div>

                <div className="flex items-center gap-3">
                  <Briefcase className="w-5 h-5 text-[#2164F3]" />
                  <div>
                    <span className="font-medium text-[#2164F3]">Level: </span>
                    <span className="text-[#2164F3]">{selectedJob.experience}</span>
                  </div>
                </div>

                <div className="flex items-start gap-3">
                  <svg className="w-5 h-5 text-[#2164F3] mt-0.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13.828 10.172a4 4 0 00-5.656 0l-4 4a4 4 0 105.656 5.656l1.102-1.101m-.758-4.899a4 4 0 005.656 0l4-4a4 4 0 00-5.656-5.656l-1.1 1.1" />
                  </svg>
                  <div className="flex-1">
                    <span className="font-medium text-[#2164F3]">Link: </span>
                    <a
                      href={selectedJob.link}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="text-[#2164F3] hover:underline break-all"
                    >
                      {selectedJob.link}
                    </a>
                  </div>
                </div>

                <div className="flex items-center gap-3">
                  <Clock className="w-5 h-5 text-[#2164F3]" />
                  <div>
                    <span className="font-medium text-[#2164F3]">Time: </span>
                    <span className="text-[#2164F3]">{selectedJob.date}</span>
                  </div>
                </div>

                {selectedJob.matchScore && (
                  <div className="flex items-center gap-3 pt-3 border-t-2 border-[#2164F3]">
                    <Target className="w-5 h-5 text-[#2164F3]" />
                    <div>
                      <span className="font-medium text-[#2164F3]">Match Score: </span>
                      <span className="font-bold text-[#2164F3]">{selectedJob.matchScore}%</span>
                    </div>
                  </div>
                )}
              </div>

              <div className="mt-6 flex gap-3">
                <button
                  onClick={() => window.open(selectedJob.link, '_blank')}
                  className="flex-1 bg-[#2164F3] hover:bg-[#1a4ec7] text-white py-3 rounded-lg font-semibold transition-colors"
                >
                  Apply Now
                </button>
                <button
                  onClick={(e) => {
                    e.stopPropagation();
                    toggleSaveJob(selectedJob.id);
                  }}
                  className={`px-6 py-3 rounded-lg font-semibold transition-colors ${selectedJob.isSaved
                      ? 'bg-[#2164F3] text-white hover:bg-[#1a4ec7]'
                      : 'border-2 border-[#2164F3] text-[#2164F3] hover:bg-blue-50'
                    }`}
                >
                  {selectedJob.isSaved ? 'Saved' : 'Save'}
                </button>
              </div>
            </div>
          </div>
        )}
      </div>

      {showLoginModal && (
        <div
          className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50"
          onClick={() => setShowLoginModal(false)}
        >
          <div
            className="bg-white rounded-lg shadow-xl w-full max-w-md p-6"
            onClick={(e) => e.stopPropagation()}
          >
            <h2 className="text-2xl font-bold text-[#2164F3] mb-4">
              Sign in
            </h2>

            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-[#2164F3] mb-1">
                  Email
                </label>
                <input
                  type="email"
                  value={loginEmail}
                  onChange={(e) => setLoginEmail(e.target.value)}
                  className="w-full px-3 py-2 border-2 border-[#2164F3] rounded focus:outline-none focus:ring-2 focus:ring-[#2164F3]"
                  placeholder="you@example.com"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-[#2164F3] mb-1">
                  Password
                </label>
                <input
                  type="password"
                  value={loginPassword}
                  onChange={(e) => setLoginPassword(e.target.value)}
                  className="w-full px-3 py-2 border-2 border-[#2164F3] rounded focus:outline-none focus:ring-2 focus:ring-[#2164F3]"
                  placeholder="••••••••"
                />
              </div>

              {loginError && (
                <p className="text-sm text-red-600">{loginError}</p>
              )}

              <button
                onClick={() => {
                  if (!loginEmail || !loginPassword) {
                    setLoginError("Email and password are required");
                    return;
                  }

                  if (!validateEmail(loginEmail)) {
                    setLoginError("Invalid email format");
                    return;
                  }

                  // UI-only success
                  setIsLoggedIn(true);
                  setUserEmail(loginEmail);

                  setLoginEmail("");
                  setLoginPassword("");
                  setLoginError("");
                  setShowLoginModal(false);
                }}
                className="w-full bg-[#2164F3] hover:bg-[#1a4ec7] text-white py-3 rounded-lg font-semibold transition-colors"
              >
                Sign in
              </button>
            </div>
          </div>
        </div>
      )}

    </div>
  );
}