"use client";

import { useState, useEffect, useRef } from "react";
import { Play, MapPin, Briefcase, DollarSign, Search, X, Bookmark, Target, History, User, Edit, Save } from "lucide-react";
import Image from "next/image";
import { createClient } from "@supabase/supabase-js";
import { useRouter } from "next/navigation";

const supabaseUrl = process.env.NEXT_PUBLIC_SUPABASE_URL!;
const supabaseKey = process.env.NEXT_PUBLIC_SUPABASE_PUBLISHABLE_DEFAULT_KEY!;
const supabase = createClient(supabaseUrl, supabaseKey);

// Get API URL from environment variable
const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
const WS_URL = API_URL.replace('http', 'ws');

interface ScrapeUpdate {
  task_id: string;
  status: "pending" | "running" | "completed" | "failed";
  jobs_found: number;
  error_message?: string;
  timestamp?: string;
  source?: string;
  spider_finished?: boolean;
  page_completed?: number;
  jobs_from_page?: number;
}

interface Job {
  id: number;
  title: string;
  company_name: string;
  location: string;
  job_type: string;
  salary?: string;
  url: string;
  description?: string;
  benefits?: string;
  priority?: boolean;
}

interface UserPreferences {
  title?: string;
  company_name?: string;
  location?: string;
  job_type?: string;
  salary?: string;
  description?: string;
  benefits?: string;
  radius?: number;
  scrape_length?: number;
}

interface UserStatistics {
  total_jobs: number;
  current_jobs: number;
  saved_jobs: number;
  completed_jobs: number;
  total_scrapes: number;
  latest_scrape?: string;
}

// Default preferences
const DEFAULT_PREFERENCES: UserPreferences = {
  title: "",
  company_name: "",
  location: "",
  job_type: "",
  salary: "",
  description: "",
  benefits: "",
  radius: undefined,
  scrape_length: 150, // MEDIUM
};

export default function JobFlowScraper() {
  const router = useRouter();
  const socketRef = useRef<WebSocket | null>(null);
  const [updates, setUpdates] = useState<ScrapeUpdate[]>([]);
  const [isScraperRunning, setIsScraperRunning] = useState(false);

  // Auth state
  const [authToken, setAuthToken] = useState<string | null>(null);
  const [displayName, setDisplayName] = useState<string>("");
  const [isLoading, setIsLoading] = useState(true);

  // New UI state for navigation
  const [activePage, setActivePage] = useState("home");
  const [isEditingPreferences, setIsEditingPreferences] = useState(false);

  // User preferences
  const [draftPreferences, setDraftPreferences] = useState<UserPreferences>(DEFAULT_PREFERENCES);
  const [preferencesError, setPreferencesError] = useState("");

  // User Statistics
  const [userStats, setUserStats] = useState<UserStatistics>({
    total_jobs: 0,
    current_jobs: 0,
    saved_jobs: 0,
    completed_jobs: 0,
    total_scrapes: 0,
    latest_scrape: undefined
  });

  // Job state
  const [jobs, setJobs] = useState<Job[]>([]);
  const [savedJobs, setSavedJobs] = useState<Job[]>([]);

  const [selectedJob, setSelectedJob] = useState<Job | null>(null);
  const [searchTerm, setSearchTerm] = useState("");
  const [savedJobsSearchTerm, setSavedJobsSearchTerm] = useState("");

  // Navigation items for sidebar
  const navigationItems = [
    { id: "home", label: "Dashboard", icon: User },
    { id: "history", label: "Job History", icon: History },
    { id: "saved", label: "Saved Jobs", icon: Bookmark },
    { id: "scrape", label: "Scrape Jobs", icon: Play },
  ];

  // Check authentication on mount
  useEffect(() => {
    const checkAuth = async () => {
      const { data: { session } } = await supabase.auth.getSession();

      if (!session) {
        router.push('/');
        return;
      }

      setAuthToken(session.access_token);
      setDisplayName(session.user.user_metadata?.display_name || "");
      setIsLoading(false);
    };

    checkAuth();

    const { data: { subscription } } = supabase.auth.onAuthStateChange((_event, session) => {
      if (!session) {
        router.push('/');
      } else {
        setAuthToken(session.access_token);
        setDisplayName(session.user.user_metadata?.display_name || "");
      }
    });

    return () => subscription.unsubscribe();
  }, [router]);

  // Helper function to get auth headers
  const getAuthHeaders = () => ({
    'Authorization': `Bearer ${authToken}`,
    'Content-Type': 'application/json',
  });

  // Fetch user preferences from API
  const fetchUserPreferences = async () => {
    if (!authToken) return;
    try {
      const response = await fetch(`${API_URL}/api/get_preferences`, {
        headers: getAuthHeaders(),
      });
      if (response.ok) {
        const prefs = await response.json();
        setDraftPreferences(prefs);
      } else {
        console.error('Failed to fetch user preferences:', response.statusText);
      }
    } catch (error) {
      console.error('Error fetching user preferences:', error);
    }
  };

  // Save user preferences to API
  const saveUserPreferences = async (prefsToSave: UserPreferences) => {
    if (!authToken) return;
    try {
      const response = await fetch(`${API_URL}/api/update_preferences`, {
        method: 'PUT',
        headers: getAuthHeaders(),
        body: JSON.stringify(prefsToSave),
      });

      if (response.ok) {
        setDraftPreferences(prefsToSave);
        setIsEditingPreferences(false);
        setPreferencesError("");
      } else {
        const errorData = await response.json();
        setPreferencesError(errorData.detail || 'Failed to save preferences');
      }
    } catch (error) {
      console.error('Error saving preferences:', error);
      setPreferencesError('Error saving preferences. Please try again.');
    }
  };

  // Load preferences from API when auth is ready
  useEffect(() => {
    if (authToken) {
      fetchUserPreferences();
    }
  }, [authToken]);

  // Fetch user statistics
  const fetchUserStatistics = async () => {
    if (!authToken) return;
    try {
      const response = await fetch(`${API_URL}/api/get_statistics`, {
        headers: getAuthHeaders(),
      });
      if (response.ok) {
        const stats = await response.json();
        setUserStats(stats);
      } else {
        console.error('Failed to fetch user statistics:', response.statusText);
      }
    } catch (error) {
      console.error('Error fetching user statistics:', error);
    }
  };

  // Load user statistics when auth is ready
  useEffect(() => {
    if (authToken) {
      fetchUserStatistics();
    }
  }, [authToken]);

  // Job API functions
  const fetchJobs = async () => {
    if (!authToken) return;
    try {
      const response = await fetch(`${API_URL}/api/get_jobs`, {
        headers: getAuthHeaders(),
      });
      if (response.ok) {
        const jobsList = await response.json();
        setJobs(jobsList || []);
      } else {
        console.error('Failed to fetch jobs:', response.statusText);
      }
    } catch (error) {
      console.error('Error fetching jobs:', error);
    }
  };

  const fetchSavedJobs = async () => {
    if (!authToken) return;
    try {
      const response = await fetch(`${API_URL}/api/get_priority_jobs`, {
        headers: getAuthHeaders(),
      });
      if (response.ok) {
        const savedJobsList = await response.json();
        setSavedJobs(savedJobsList || []);
      } else {
        console.error('Failed to fetch saved jobs:', response.statusText);
      }
    } catch (error) {
      console.error('Error fetching saved jobs:', error);
    }
  };

  const searchJobs = async (query: string) => {
    if (!authToken) return;
    if (!query.trim()) {
      fetchJobs();
      return;
    }

    try {
      const response = await fetch(`${API_URL}/api/search_jobs?q=${encodeURIComponent(query)}`, {
        headers: getAuthHeaders(),
      });
      if (response.ok) {
        const searchResults = await response.json();
        setJobs(searchResults || []);
      } else {
        console.error('Failed to search jobs:', response.statusText);
      }
    } catch (error) {
      console.error('Error searching jobs:', error);
    }
  };

  const toggleJobPriority = async (jobId: number) => {
    if (!authToken) return;
    // Optimistically update the selected job's priority immediately
    if (selectedJob && selectedJob.id === jobId) {
      setSelectedJob({ ...selectedJob, priority: !selectedJob.priority });
    }

    try {
      const response = await fetch(`${API_URL}/api/toggle_job_priority/${jobId}`, {
        method: 'PUT',
        headers: getAuthHeaders(),
      });
      if (response.ok) {
        // Refresh both job lists
        fetchJobs();
        fetchSavedJobs();
        fetchUserStatistics(); // Update statistics
      } else {
        console.error('Failed to toggle job priority:', response.statusText);
        // Revert the optimistic update on error
        if (selectedJob && selectedJob.id === jobId) {
          setSelectedJob({ ...selectedJob, priority: !selectedJob.priority });
        }
      }
    } catch (error) {
      console.error('Error toggling job priority:', error);
      // Revert the optimistic update on error
      if (selectedJob && selectedJob.id === jobId) {
        setSelectedJob({ ...selectedJob, priority: !selectedJob.priority });
      }
    }
  };

  const deleteJob = async (jobId: number) => {
    if (!authToken) return;
    try {
      const response = await fetch(`${API_URL}/api/delete_job_by_id/${jobId}`, {
        method: 'DELETE',
        headers: getAuthHeaders(),
      });
      if (response.ok) {
        // Refresh both job lists
        fetchJobs();
        fetchSavedJobs();
        fetchUserStatistics(); // Update statistics
        // Close modal if the deleted job was selected
        if (selectedJob && selectedJob.id === jobId) {
          setSelectedJob(null);
        }
      } else {
        console.error('Failed to delete job:', response.statusText);
      }
    } catch (error) {
      console.error('Error deleting job:', error);
    }
  };

  const completeJob = async (jobId: number) => {
    if (!authToken) return;
    try {
      const response = await fetch(`${API_URL}/api/job_complete/${jobId}`, {
        headers: getAuthHeaders(),
      });
      if (response.ok) {
        // Refresh both job lists
        fetchJobs();
        fetchSavedJobs();
        fetchUserStatistics(); // Update statistics
        // Close modal if the completed job was selected
        if (selectedJob && selectedJob.id === jobId) {
          setSelectedJob(null);
        }
      } else {
        console.error('Failed to complete job:', response.statusText);
      }
    } catch (error) {
      console.error('Error completing job:', error);
    }
  };

  // Load jobs when auth is ready
  useEffect(() => {
    if (authToken) {
      fetchJobs();
      fetchSavedJobs();
    }
  }, [authToken]);

  useEffect(() => {
    if (!authToken) return;

    const socket = new WebSocket(`${WS_URL}/ws/scrape?token=${authToken}`);
    socketRef.current = socket;

    socket.onopen = () => {
      console.log("WebSocket connected");
    };

    socket.onmessage = (event) => {
      try {
        const data: ScrapeUpdate = JSON.parse(event.data);
        console.log("Received websocket data:", data);
        setUpdates((prev) => [...prev, { ...data, timestamp: new Date().toLocaleTimeString() }]);

        // Reset scraper running state when scrape is completed or failed
        if (data.status === 'completed' || data.status === 'failed') {
          setIsScraperRunning(false);
          // Refresh user statistics and jobs after scrape completion
          if (data.status === 'completed') {
            fetchUserStatistics();
            fetchJobs();
            fetchSavedJobs();
          }
        }
      } catch (e) {
        console.error("Failed to parse message:", event.data);
      }
    };

    socket.onclose = () => console.log("WebSocket disconnected");
    socket.onerror = (error) => console.error("WebSocket error:", error);

    return () => socket.close();
  }, [authToken]);

  // Save preferences
  const handleSavePreferences = () => {
    // Basic validation
    if (!draftPreferences.title || !draftPreferences.location) {
      setPreferencesError("Title and location are required");
      return;
    }

    saveUserPreferences(draftPreferences);
  };

  const handleStartScrape = async () => {
    if (!authToken || isScraperRunning) return;

    setIsScraperRunning(true);

    try {
      const response = await fetch(`${API_URL}/api/scrape`, {
        method: 'POST',
        headers: getAuthHeaders(),
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        const errorDetail = errorData.detail || `HTTP error! status: ${response.status}`;
        throw new Error(errorDetail);
      }

      const result = await response.json();
      console.log('Scrape started:', result);

      // Add initial update to show scrape has started
      setUpdates((prev) => [...prev, {
        ...result,
        task_id: 'manual-trigger',
        timestamp: new Date().toLocaleTimeString()
      }]);

    } catch (error) {
      console.error('Error starting scrape:', error);
      setIsScraperRunning(false);

      let errorMessage = 'Unknown error';
      if (error instanceof Error) {
        if (error.message.includes('No preferences set')) {
          errorMessage = 'Please set your Job Title and Location in Preferences before starting a scrape';
        } else {
          errorMessage = error.message;
        }
      }

      // Add error update
      setUpdates((prev) => [...prev, {
        task_id: 'manual-trigger',
        status: 'failed' as const,
        jobs_found: 0,
        error_message: `Failed to start scrape: ${errorMessage}`,
        timestamp: new Date().toLocaleTimeString()
      }]);
    }
  };

  // Handle search with debouncing
  useEffect(() => {
    const timeoutId = setTimeout(() => {
      if (searchTerm.trim()) {
        searchJobs(searchTerm);
      } else {
        fetchJobs();
      }
    }, 300);

    return () => clearTimeout(timeoutId);
  }, [searchTerm]);

  // Filter saved jobs locally
  const filteredSavedJobs = savedJobs.filter(job =>
    job.title.toLowerCase().includes(savedJobsSearchTerm.toLowerCase()) ||
    job.company_name.toLowerCase().includes(savedJobsSearchTerm.toLowerCase()) ||
    job.location.toLowerCase().includes(savedJobsSearchTerm.toLowerCase())
  );

  const stats = [
    { label: "Total Jobs", value: userStats.total_jobs.toString() },
    { label: "Current Jobs", value: userStats.current_jobs.toString() },
    { label: "Saved Jobs", value: userStats.saved_jobs.toString() },
    { label: "Completed", value: userStats.completed_jobs.toString() },
    { label: "Total Scrapes", value: userStats.total_scrapes.toString() },
    { label: "Last Scrape", value: userStats.latest_scrape ? new Date(userStats.latest_scrape).toLocaleDateString() : 'Never' },
  ];

  if (isLoading) {
    return (
      <div className="flex h-screen items-center justify-center bg-gray-50">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto"></div>
          <p className="mt-4 text-gray-600">Loading...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="flex h-screen bg-gray-50 overflow-hidden">
      {/* Sidebar */}
      <aside className="w-64 border-r border-gray-200 bg-white flex flex-col">
        <div className="flex h-16 items-center gap-2 border-b border-gray-200 px-6 flex-shrink-0">
          <Image
            src="/Adobe Express - file.png"
            alt="JobFlow Logo"
            width={32}
            height={32}
            className="rounded-lg"
          />
          <span className="text-lg font-semibold text-gray-900">JobFlow</span>
        </div>

        <nav className="flex flex-col gap-1 p-4 flex-1">
          {navigationItems.map((item) => {
            const Icon = item.icon;
            return (
              <button
                key={item.id}
                onClick={() => setActivePage(item.id)}
                className={`flex items-center gap-3 rounded-lg px-3 py-2.5 text-sm font-medium transition-colors ${
                  activePage === item.id
                    ? "bg-blue-600 text-white"
                    : "text-gray-600 hover:bg-gray-100 hover:text-gray-900"
                }`}
              >
                <Icon className="h-5 w-5" />
                {item.label}
              </button>
            );
          })}
        </nav>

        <div className="border-t border-gray-200 px-6 py-4 flex-shrink-0">
          <p className="text-xs text-gray-500 text-center">Copyright © 2026 JobFlow. All rights reserved.</p>
        </div>
      </aside>

      {/* Main Content */}
      <main className="flex-1 h-full flex flex-col overflow-hidden">
        <div className="flex-1 overflow-y-auto">
          <div className="mx-auto max-w-7xl h-full p-6 lg:p-8">
            {activePage === "home" && (
              <div className="flex flex-col h-full justify-center">
                <div className="text-center space-y-4 mb-16">
                  <div className="flex justify-center mb-6">
                    <Image
                      src="/Adobe Express - file.png"
                      alt="JobFlow Logo"
                      width={120}
                      height={120}
                      className="rounded-2xl"
                    />
                  </div>
                  <h1 className="text-5xl font-bold tracking-tight text-balance">Welcome back{displayName ? `, ${displayName}` : ""}</h1>
                </div>

                <div className="grid gap-4 md:grid-cols-3 lg:grid-cols-6 max-w-5xl mx-auto">
                  {stats.map((stat) => (
                    <div key={stat.label} className="bg-white rounded-lg shadow-sm border border-gray-200 text-center p-4 flex flex-col justify-center">
                      <div className="pb-2">
                        <h3 className={`font-bold text-gray-900 ${stat.label === 'Last Scrape' ? 'text-xl' : 'text-3xl'}`}>{stat.value}</h3>
                      </div>
                      <div>
                        <p className={`font-medium text-gray-600 leading-tight ${stat.label === 'Last Scrape' ? 'text-[10px]' : 'text-xs'}`}>{stat.label}</p>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {activePage === "history" && (
              <div className="flex flex-col h-full">
                <div className="space-y-2 flex-shrink-0">
                  <h1 className="text-3xl font-bold tracking-tight">Job History</h1>
                  <p className="text-gray-600">All jobs discovered and tracked by JobFlow</p>
                </div>

                <div className="flex gap-3 mt-6 flex-shrink-0">
                  <div className="relative flex-1">
                    <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-gray-400" />
                    <input
                      className="w-full pl-9 pr-4 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                      placeholder="Search by title, company, or location..."
                      value={searchTerm}
                      onChange={(e) => setSearchTerm(e.target.value)}
                    />
                  </div>
                </div>

                <div className="flex-1 overflow-y-auto mt-6 space-y-3">
                  {jobs.length === 0 ? (
                    <div className="bg-white rounded-lg shadow-sm border border-gray-200 flex items-center justify-center py-12">
                      <div className="text-center">
                        <p className="text-gray-500">No jobs available</p>
                        <p className="text-gray-400 text-sm mt-2">Try starting a scrape to find jobs</p>
                      </div>
                    </div>
                  ) : (
                    jobs.map((job) => (
                      <div key={job.id} className={`${job.priority ? 'bg-blue-50 border-blue-200' : 'bg-white border-gray-200'} rounded-lg shadow-sm transition-shadow hover:shadow-md`}>
                        <div className="p-6">
                          <div className="flex items-start justify-between">
                            <div className="space-y-2 flex-1">
                              <div className="flex items-start justify-between">
                                <div>
                                  <h3 className="text-lg font-semibold text-gray-900">{job.title}</h3>
                                  <p className="text-sm text-gray-600">{job.company_name}</p>
                                </div>
                                {job.priority && (
                                  <span className="rounded-full px-3 py-1 text-xs font-medium bg-blue-100 text-blue-800">
                                    Priority
                                  </span>
                                )}
                              </div>
                              <div className="flex flex-wrap gap-4 text-sm text-gray-600">
                                <span className="flex items-center gap-1.5">
                                  <MapPin className="h-4 w-4" />
                                  {job.location}
                                </span>
                                {job.salary && (
                                  <span className="flex items-center gap-1.5">
                                    <DollarSign className="h-4 w-4" />
                                    {job.salary}
                                  </span>
                                )}
                                <span className="flex items-center gap-1.5">
                                  <Briefcase className="h-4 w-4" />
                                  {job.job_type}
                                </span>
                              </div>
                              <div className="flex gap-2 pt-2">
                                <button
                                  onClick={() => window.open(job.url, '_blank')}
                                  className="px-3 py-1.5 text-sm bg-blue-600 hover:bg-blue-700 text-white rounded-md transition-colors"
                                >
                                  Apply Now
                                </button>
                                <button
                                  onClick={() => setSelectedJob(job)}
                                  className="px-3 py-1.5 text-sm bg-gray-100 hover:bg-gray-200 text-gray-700 rounded-md transition-colors"
                                >
                                  View Details
                                </button>
                                <button
                                  onClick={() => toggleJobPriority(job.id)}
                                  className="p-1.5 text-gray-400 hover:text-blue-500 rounded-md transition-colors"
                                >
                                  <Bookmark className={`h-4 w-4 ${job.priority ? 'fill-blue-500 text-blue-500' : ''}`} />
                                </button>
                              </div>
                            </div>
                          </div>
                        </div>
                      </div>
                    ))
                  )}
                </div>
              </div>
            )}

            {activePage === "saved" && (
              <div className="flex flex-col h-full">
                <div className="space-y-2 flex-shrink-0">
                  <h1 className="text-3xl font-bold tracking-tight">Saved Jobs</h1>
                  <p className="text-gray-600">Jobs you've bookmarked for later review</p>
                </div>

                <div className="flex gap-3 mt-6 flex-shrink-0">
                  <div className="relative flex-1">
                    <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-gray-400" />
                    <input
                      className="w-full pl-9 pr-4 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                      placeholder="Search by title, company, or location..."
                      value={savedJobsSearchTerm}
                      onChange={(e) => setSavedJobsSearchTerm(e.target.value)}
                    />
                  </div>
                </div>

                {filteredSavedJobs.length > 0 ? (
                  <div className="flex-1 overflow-y-auto mt-6 space-y-3">
                    {filteredSavedJobs.map((job) => (
                      <div key={job.id} className="bg-blue-50 rounded-lg shadow-sm border border-blue-200 transition-shadow hover:shadow-md">
                        <div className="p-6">
                          <div className="flex items-start justify-between">
                            <div className="space-y-2 flex-1">
                              <div>
                                <h3 className="text-lg font-semibold text-gray-900">{job.title}</h3>
                                <p className="text-sm text-gray-600">{job.company_name}</p>
                              </div>
                              <div className="flex flex-wrap gap-4 text-sm text-gray-600">
                                <span className="flex items-center gap-1.5">
                                  <MapPin className="h-4 w-4" />
                                  {job.location}
                                </span>
                                {job.salary && (
                                  <span className="flex items-center gap-1.5">
                                    <DollarSign className="h-4 w-4" />
                                    {job.salary}
                                  </span>
                                )}
                                <span className="flex items-center gap-1.5">
                                  <Briefcase className="h-4 w-4" />
                                  {job.job_type}
                                </span>
                              </div>
                              <div className="flex gap-2 pt-2">
                                <button
                                  onClick={() => window.open(job.url, '_blank')}
                                  className="px-3 py-1.5 text-sm bg-blue-600 hover:bg-blue-700 text-white rounded-md transition-colors"
                                >
                                  Apply Now
                                </button>
                                <button
                                  onClick={() => setSelectedJob(job)}
                                  className="px-3 py-1.5 text-sm bg-gray-100 hover:bg-gray-200 text-gray-700 rounded-md transition-colors"
                                >
                                  View Details
                                </button>
                                <button
                                  onClick={() => toggleJobPriority(job.id)}
                                  className="p-1.5 text-blue-500 hover:text-blue-600 rounded-md transition-colors"
                                >
                                  <Bookmark className="h-4 w-4 fill-current" />
                                </button>
                              </div>
                            </div>
                          </div>
                        </div>
                      </div>
                    ))}
                  </div>
                ) : (
                  <div className="bg-white rounded-lg shadow-sm border border-gray-200 flex-1 flex items-center justify-center mt-6">
                    <div className="flex flex-col items-center justify-center py-12">
                      <Bookmark className="h-12 w-12 text-gray-400 mb-4" />
                      <p className="text-gray-500">No saved jobs yet</p>
                      <p className="text-gray-400 text-sm mt-2">Click the bookmark icon on jobs to save them here</p>
                    </div>
                  </div>
                )}
              </div>
            )}

            {activePage === "scrape" && (
              <div className="flex flex-col h-full">
                <div className="flex items-center justify-between flex-shrink-0">
                  <div className="space-y-2">
                    <h1 className="text-3xl font-bold tracking-tight">Scrape Jobs</h1>
                    <p className="text-gray-600">
                      Configure and run job scraping to discover new opportunities
                    </p>
                  </div>
                  <button
                    onClick={() => isEditingPreferences ? handleSavePreferences() : setIsEditingPreferences(true)}
                    className={`flex items-center gap-2 px-4 py-2 text-sm rounded-md transition-colors ${
                      isEditingPreferences
                        ? 'bg-blue-600 hover:bg-blue-700 text-white'
                        : 'bg-gray-100 hover:bg-gray-200 text-gray-700'
                    }`}
                  >
                    {isEditingPreferences ? (
                      <>
                        <Save className="h-4 w-4" />
                        Save
                      </>
                    ) : (
                      <>
                        <Edit className="h-4 w-4" />
                        Edit
                      </>
                    )}
                  </button>
                </div>

                <div className="grid gap-6 lg:grid-cols-2 mt-6 flex-1 items-start">
                  <div className="space-y-6">
                    <div className="bg-white rounded-lg shadow-sm border border-gray-200">
                      <div className="p-6 border-b border-gray-200">
                        <h3 className="text-lg font-semibold">Job Scraper</h3>
                        <p className="text-gray-600 text-sm">Define what jobs you're looking for</p>
                      </div>
                      <div className="p-6 space-y-4">
                        <div className="space-y-2">
                          <label className="text-sm font-medium text-gray-700">Job Title</label>
                          <input
                            value={draftPreferences.title || ""}
                            onChange={(e) => setDraftPreferences({ ...draftPreferences, title: e.target.value })}
                            disabled={!isEditingPreferences}
                            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent disabled:bg-gray-50 disabled:text-gray-500"
                            placeholder="e.g., Software Engineer, Product Manager"
                          />
                        </div>
                        <div className="space-y-2">
                          <label className="text-sm font-medium text-gray-700">Location</label>
                          <input
                            value={draftPreferences.location || ""}
                            onChange={(e) => setDraftPreferences({ ...draftPreferences, location: e.target.value })}
                            disabled={!isEditingPreferences}
                            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent disabled:bg-gray-50 disabled:text-gray-500"
                            placeholder="e.g., San Francisco, Remote"
                          />
                        </div>

                        <div className="space-y-2">
                          <label className="text-sm font-medium text-gray-700">Scrape Length</label>
                          <div className="flex gap-2">
                            <button
                              onClick={() => {
                                const newPreferences = { ...draftPreferences, scrape_length: 50 };
                                setDraftPreferences(newPreferences);
                                saveUserPreferences(newPreferences);
                              }}
                              className={`flex-1 px-3 py-2 text-sm rounded-md transition-colors ${
                                draftPreferences.scrape_length === 50
                                  ? "bg-blue-600 text-white"
                                  : "bg-gray-100 text-gray-700 hover:bg-gray-200"
                              }`}
                            >
                              Short (50 jobs)
                            </button>
                            <button
                              onClick={() => {
                                const newPreferences = { ...draftPreferences, scrape_length: 150 };
                                setDraftPreferences(newPreferences);
                                saveUserPreferences(newPreferences);
                              }}
                              className={`flex-1 px-3 py-2 text-sm rounded-md transition-colors ${
                                draftPreferences.scrape_length === 150
                                  ? "bg-blue-600 text-white"
                                  : "bg-gray-100 text-gray-700 hover:bg-gray-200"
                              }`}
                            >
                              Medium (150 jobs)
                            </button>
                            <button
                              onClick={() => {
                                const newPreferences = { ...draftPreferences, scrape_length: 250 };
                                setDraftPreferences(newPreferences);
                                saveUserPreferences(newPreferences);
                              }}
                              className={`flex-1 px-3 py-2 text-sm rounded-md transition-colors ${
                                draftPreferences.scrape_length === 250
                                  ? "bg-blue-600 text-white"
                                  : "bg-gray-100 text-gray-700 hover:bg-gray-200"
                              }`}
                            >
                              Long (250 jobs)
                            </button>
                          </div>
                        </div>

                        {preferencesError && (
                          <div className="p-3 bg-red-50 border border-red-200 rounded text-red-700 text-sm">
                            {preferencesError}
                          </div>
                        )}


                        <button
                          onClick={handleStartScrape}
                          disabled={isScraperRunning}
                          className="w-full px-4 py-2 bg-green-600 hover:bg-green-700 disabled:bg-gray-400 text-white rounded-md transition-colors"
                        >
                          {isScraperRunning ? "Scraping..." : "Start Scrape"}
                        </button>
                      </div>
                    </div>

                    <div className="bg-white rounded-lg shadow-sm border border-gray-200">
                      <div className="p-6 border-b border-gray-200">
                        <h3 className="text-lg font-semibold">System Updates</h3>
                        <p className="text-gray-600 text-sm">Recent activity and system notifications</p>
                      </div>
                      <div className="p-5">
                        <div className="space-y-4 h-[97px] max-h-[97px] overflow-y-auto">
                          {updates.length === 0 ? (
                            <p className="text-gray-500 text-sm">No updates yet. Start a scrape to see messages.</p>
                          ) : (
                            updates.slice().reverse().map((update, i) => (
                              <div key={i} className="flex gap-4 text-sm">
                                <div className={`h-2 w-2 rounded-full mt-1.5 flex-shrink-0 ${
                                  update.status === 'completed' ? 'bg-green-500' :
                                  update.status === 'failed' ? 'bg-red-500' :
                                  update.status === 'running' ? 'bg-blue-500' :
                                  'bg-gray-400'
                                }`} />
                                <div>
                                  <p className="font-medium text-gray-900">
                                    {update.jobs_found} jobs found
                                    {update.page_completed && ` (page ${update.page_completed})`}
                                  </p>
                                  <p className="text-gray-600">Status: {update.status.toUpperCase()}</p>
                                  {update.error_message && (
                                    <p className="text-red-600">{update.error_message}</p>
                                  )}
                                  <p className="text-xs text-gray-500 mt-1">{update.timestamp}</p>
                                </div>
                              </div>
                            ))
                          )}
                        </div>
                      </div>
                    </div>
                  </div>

                  <div className="bg-white rounded-lg shadow-sm border border-gray-200">
                    <div className="p-6 border-b border-gray-200">
                      <h3 className="text-lg font-semibold">Search Preferences</h3>
                      <p className="text-gray-600 text-sm">Advanced filters to narrow your search</p>
                    </div>
                    <div className="p-6 space-y-6">
                      <div className="space-y-2">
                        <label className="text-sm font-medium text-gray-700">Company Name</label>
                        <input
                          value={draftPreferences.company_name || ""}
                          onChange={(e) => setDraftPreferences({ ...draftPreferences, company_name: e.target.value })}
                          disabled={!isEditingPreferences}
                          className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent disabled:bg-gray-50 disabled:text-gray-500"
                          placeholder="e.g., Google, Microsoft"
                        />
                      </div>
                      <div className="space-y-2">
                        <label className="text-sm font-medium text-gray-700">Job Type</label>
                        <input
                          value={draftPreferences.job_type || ""}
                          onChange={(e) => setDraftPreferences({ ...draftPreferences, job_type: e.target.value })}
                          disabled={!isEditingPreferences}
                          className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent disabled:bg-gray-50 disabled:text-gray-500"
                          placeholder="e.g., Full-time, Contract"
                        />
                      </div>
                      <div className="space-y-2">
                        <label className="text-sm font-medium text-gray-700">Salary</label>
                        <input
                          value={draftPreferences.salary || ""}
                          onChange={(e) => setDraftPreferences({ ...draftPreferences, salary: e.target.value })}
                          disabled={!isEditingPreferences}
                          className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent disabled:bg-gray-50 disabled:text-gray-500"
                          placeholder="e.g., $100k-$150k"
                        />
                      </div>
                      <div className="space-y-2">
                        <label className="text-sm font-medium text-gray-700">Description Keywords</label>
                        <input
                          value={draftPreferences.description || ""}
                          onChange={(e) => setDraftPreferences({ ...draftPreferences, description: e.target.value })}
                          disabled={!isEditingPreferences}
                          className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent disabled:bg-gray-50 disabled:text-gray-500"
                          placeholder="e.g., Git, AWS"
                        />
                      </div>
                      <div className="space-y-2">
                        <label className="text-sm font-medium text-gray-700">Benefits</label>
                        <input
                          value={draftPreferences.benefits || ""}
                          onChange={(e) => setDraftPreferences({ ...draftPreferences, benefits: e.target.value })}
                          disabled={!isEditingPreferences}
                          className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent disabled:bg-gray-50 disabled:text-gray-500"
                          placeholder="e.g., Insurance, Dental"
                        />
                      </div>
                      <div className="space-y-2">
                        <label className="text-sm font-medium text-gray-700">Search Radius (km)</label>
                        <input
                          type="number"
                          value={draftPreferences.radius || ""}
                          onChange={(e) => setDraftPreferences({ ...draftPreferences, radius: e.target.value ? parseInt(e.target.value) : undefined })}
                          disabled={!isEditingPreferences}
                          className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent disabled:bg-gray-50 disabled:text-gray-500"
                          placeholder="e.g., 50"
                        />
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            )}
          </div>
        </div>
      </main>

      {/* Job Detail Modal */}
      {selectedJob && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50" onClick={() => setSelectedJob(null)}>
          <div className="bg-white rounded-lg shadow-xl max-w-2xl w-full max-h-[90vh] overflow-y-auto p-6" onClick={(e) => e.stopPropagation()}>
            <div className="flex items-start justify-between mb-6">
              <h2 className="text-2xl font-bold text-gray-900">{selectedJob.title}</h2>
              <button
                onClick={() => setSelectedJob(null)}
                className="text-gray-400 hover:text-gray-600"
              >
                <X className="w-6 h-6" />
              </button>
            </div>

            <div className="space-y-4">
              <div className="flex items-center gap-3">
                <Briefcase className="w-5 h-5 text-gray-400" />
                <div>
                  <span className="font-medium text-gray-700">Company: </span>
                  <span className="text-gray-900">{selectedJob.company_name}</span>
                </div>
              </div>

              <div className="flex items-center gap-3">
                <MapPin className="w-5 h-5 text-gray-400" />
                <div>
                  <span className="font-medium text-gray-700">Location: </span>
                  <span className="text-gray-900">{selectedJob.location}</span>
                </div>
              </div>

              <div className="flex items-center gap-3">
                <Briefcase className="w-5 h-5 text-gray-400" />
                <div>
                  <span className="font-medium text-gray-700">Job Type: </span>
                  <span className="text-gray-900">{selectedJob.job_type}</span>
                </div>
              </div>

              {selectedJob.salary && (
                <div className="flex items-center gap-3">
                  <DollarSign className="w-5 h-5 text-gray-400" />
                  <div>
                    <span className="font-medium text-gray-700">Salary: </span>
                    <span className="text-gray-900">{selectedJob.salary}</span>
                  </div>
                </div>
              )}

              {selectedJob.description && (
                <div className="flex items-start gap-3">
                  <Target className="w-5 h-5 text-gray-400 mt-0.5" />
                  <div className="flex-1">
                    <span className="font-medium text-gray-700">Description: </span>
                    <p className="text-gray-900 mt-1">{selectedJob.description}</p>
                  </div>
                </div>
              )}

              {selectedJob.benefits && (
                <div className="flex items-start gap-3">
                  <Bookmark className="w-5 h-5 text-gray-400 mt-0.5" />
                  <div className="flex-1">
                    <span className="font-medium text-gray-700">Benefits: </span>
                    <p className="text-gray-900 mt-1">{selectedJob.benefits}</p>
                  </div>
                </div>
              )}

              <div className="flex items-center gap-3 pt-3 border-t border-gray-100">
                <span className={`px-3 py-1 rounded-full text-sm font-medium ${
                  selectedJob.priority
                    ? 'bg-blue-100 text-blue-800'
                    : 'bg-gray-100 text-gray-600'
                }`}>
                  {selectedJob.priority ? 'Priority Job' : 'Regular Job'}
                </span>
              </div>
            </div>

            <div className="mt-6 grid grid-cols-2 gap-3">
              <button
                onClick={() => window.open(selectedJob.url, '_blank')}
                className="bg-blue-600 hover:bg-blue-700 text-white py-3 rounded-lg font-semibold transition-colors"
              >
                Apply Now
              </button>
              <button
                onClick={() => toggleJobPriority(selectedJob.id)}
                className={`py-3 rounded-lg font-semibold transition-colors ${
                  selectedJob.priority
                    ? 'bg-blue-100 text-blue-800 hover:bg-blue-200'
                    : 'border-2 border-blue-600 text-blue-600 hover:bg-blue-50'
                }`}
              >
                {selectedJob.priority ? 'Remove Priority' : 'Add Priority'}
              </button>
            </div>

            <div className="mt-3 grid grid-cols-2 gap-3">
              <button
                onClick={() => completeJob(selectedJob.id)}
                className="bg-green-600 hover:bg-green-700 text-white py-3 rounded-lg font-semibold transition-colors"
              >
                Mark Complete
              </button>
              <button
                onClick={() => deleteJob(selectedJob.id)}
                className="bg-red-600 hover:bg-red-700 text-white py-3 rounded-lg font-semibold transition-colors"
              >
                Delete Job
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
