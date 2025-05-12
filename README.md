# OpenGraphIntel

![License](https://img.shields.io/github/license/edwardlc0000/OpenGraphIntel) [![codecov](https://codecov.io/gh/edwardlc0000/OpenGraphIntel/graph/badge.svg?token=AP2VHX57NM)](https://codecov.io/gh/edwardlc0000/OpenGraphIntel)

OpenGraphIntel is an open-source tool designed to explore sanctions networks and visualize the connections between entities. It provides a user-friendly interface for searching and analyzing data, making it easier to understand complex relationships.

## Architecture

The architecture of OpenGraphIntel is designed to be modular and scalable. It consists of several components that work together to provide a seamless user experience. The main components include:

- **Frontend**: The user interface built with React, allowing users to interact with the application and visualize data.
- **Backend**: The server-side component built with FastAPI, responsible for handling requests, processing data, and serving the frontend.
	- **Gateway**: The gateway component that acts as a reverse proxy, routing requests to the appropriate backend services.
	- **GraphQL API**: The GraphQL API that provides a flexible and efficient way to query data from the backend. It allows users to retrieve specific data based on their needs, reducing the amount of data transferred over the network.
	- **Ingestion**: The ingestion component that handles the process of collecting and processing data from various sources.
	- **LLM Query**: The LLM query component that uses large language models to process and analyze data, providing advanced search capabilities and insights.
	- **Matcher**: The matcher component that uses machine learning algorithms to identify and match entities based on their attributes and relationships. This component is responsible for finding connections between entities and providing insights into their relationships.
	- **NLP Enrichment**: The NLP enrichment component that uses natural language processing techniques to extract and enrich data, providing additional context and insights into the entities and relationships.
- **Data Layer**: The data layer consists of several components that manage the storage and retrieval of data:
	- **Database**: A PostgreSQL database that stores the data used by the application, including entities, relationships, and user information.
	- **Graph Database**: A Neo4j database that stores the graph data, allowing for efficient querying and visualization of complex relationships.
	- **Vector Store**: A Milvus vector store that stores embeddings for efficient similarity search and retrieval of related entities.

