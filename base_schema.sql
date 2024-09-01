-- IndependentMedia definition

CREATE TABLE IndependentMedia(
	IndependentMediaId  INTEGER NOT NULL PRIMARY KEY,
	OriginalFilename    TEXT NOT NULL,
	FilePath            TEXT NOT NULL UNIQUE,
	MimeType            TEXT NOT NULL,  
	Hash                TEXT NOT NULL);


-- LastModified definition

CREATE TABLE "LastModified"(LastModified TEXT NOT NULL);


-- Location definition

CREATE TABLE "Location"(
	LocationId      INTEGER NOT NULL PRIMARY KEY,
	BookNumber      INTEGER,
	ChapterNumber   INTEGER,
	DocumentId      INTEGER,
	Track           INTEGER,
	IssueTagNumber  INTEGER NOT NULL DEFAULT 0,
	KeySymbol       TEXT,
	MepsLanguage    INTEGER,
	Type            INTEGER NOT NULL,
	Title           TEXT,
	UNIQUE(BookNumber, ChapterNumber, KeySymbol, MepsLanguage, Type),
	UNIQUE(KeySymbol, IssueTagNumber, MepsLanguage, DocumentId, Track, Type)
	);


-- PlaylistItemAccuracy definition

CREATE TABLE PlaylistItemAccuracy(
	PlaylistItemAccuracyId  INTEGER NOT NULL PRIMARY KEY,
	Description             TEXT NOT NULL UNIQUE);


-- Tag definition

CREATE TABLE Tag(
	TagId          INTEGER NOT NULL PRIMARY KEY,
	Type           INTEGER NOT NULL,
	Name           TEXT NOT NULL,
	UNIQUE(Type, Name));


-- Bookmark definition

CREATE TABLE "Bookmark" (
    BookmarkId              INTEGER NOT NULL PRIMARY KEY,
    LocationId              INTEGER NOT NULL,
    PublicationLocationId   INTEGER NOT NULL,
    Slot                    INTEGER NOT NULL,
    Title                   TEXT NOT NULL,
    Snippet                 TEXT,
    BlockType               INTEGER NOT NULL DEFAULT 0,
    BlockIdentifier         INTEGER,
    FOREIGN KEY(LocationId) REFERENCES Location(LocationId),
    FOREIGN KEY(PublicationLocationId) REFERENCES Location(LocationId),
    CONSTRAINT PublicationLocationId_Slot UNIQUE (PublicationLocationId, Slot)
);


-- InputField definition

CREATE TABLE "InputField"(
	LocationId  INTEGER NOT NULL,
	TextTag     TEXT NOT NULL,
	Value       TEXT NOT NULL,
	FOREIGN KEY (LocationId) REFERENCES Location (LocationId),
	CONSTRAINT LocationId_TextTag PRIMARY KEY (LocationId, TextTag));


-- PlaylistItem definition

CREATE TABLE "PlaylistItem"(            
	PlaylistItemId           INTEGER NOT NULL PRIMARY KEY,
	Label                    TEXT NOT NULL,
	StartTrimOffsetTicks     INTEGER,
	EndTrimOffsetTicks       INTEGER,
	Accuracy                 INTEGER NOT NULL,
	EndAction                INTEGER NOT NULL,
	ThumbnailFilePath        TEXT,
	FOREIGN KEY(Accuracy) REFERENCES PlaylistItemAccuracy(PlaylistItemAccuracyId),
	FOREIGN KEY(ThumbnailFilePath) REFERENCES IndependentMedia(FilePath)
);


-- PlaylistItemIndependentMediaMap definition

CREATE TABLE PlaylistItemIndependentMediaMap(
	PlaylistItemId      INTEGER NOT NULL,
	IndependentMediaId  INTEGER NOT NULL,
	DurationTicks       INTEGER NOT NULL,
	PRIMARY KEY(PlaylistItemId, IndependentMediaId),
	FOREIGN KEY(PlaylistItemId) REFERENCES PlaylistItem(PlaylistItemId),
	FOREIGN KEY(IndependentMediaId) REFERENCES IndependentMedia(IndependentMediaId)) 
WITHOUT ROWID;



-- PlaylistItemLocationMap definition

CREATE TABLE PlaylistItemLocationMap(
	PlaylistItemId      INTEGER NOT NULL,
	LocationId          INTEGER NOT NULL,
	MajorMultimediaType INTEGER NOT NULL,
	BaseDurationTicks   INTEGER,
	PRIMARY KEY(PlaylistItemId, LocationId),
	FOREIGN KEY(PlaylistItemId) REFERENCES PlaylistItem(PlaylistItemId),
	FOREIGN KEY(LocationId) REFERENCES Location(LocationId)) 
WITHOUT ROWID;



-- PlaylistItemMarker definition

CREATE TABLE PlaylistItemMarker(
	PlaylistItemMarkerId        INTEGER NOT NULL PRIMARY KEY,
	PlaylistItemId              INTEGER NOT NULL,
	Label                       TEXT NOT NULL,
	StartTimeTicks              INTEGER NOT NULL,
	DurationTicks               INTEGER NOT NULL,
	EndTransitionDurationTicks  INTEGER NOT NULL,
	UNIQUE(PlaylistItemId, StartTimeTicks),
	FOREIGN KEY(PlaylistItemId) REFERENCES PlaylistItem(PlaylistItemId));


-- PlaylistItemMarkerBibleVerseMap definition

CREATE TABLE PlaylistItemMarkerBibleVerseMap(
	PlaylistItemMarkerId        INTEGER NOT NULL,
	VerseId                     INTEGER NOT NULL,
	PRIMARY KEY(PlaylistItemMarkerId, VerseId),
	FOREIGN KEY(PlaylistItemMarkerId) REFERENCES PlaylistItemMarker(PlaylistItemMarkerId)) 
WITHOUT ROWID;


-- PlaylistItemMarkerParagraphMap definition

CREATE TABLE PlaylistItemMarkerParagraphMap(
	PlaylistItemMarkerId        INTEGER NOT NULL,
	MepsDocumentId              INTEGER NOT NULL,
	ParagraphIndex              INTEGER NOT NULL,
	MarkerIndexWithinParagraph  INTEGER NOT NULL,
	PRIMARY KEY(PlaylistItemMarkerId, MepsDocumentId, ParagraphIndex, MarkerIndexWithinParagraph),
	FOREIGN KEY(PlaylistItemMarkerId) REFERENCES PlaylistItemMarker(PlaylistItemMarkerId)) 
WITHOUT ROWID;


-- UserMark definition

CREATE TABLE "UserMark" (
    UserMarkId      INTEGER NOT NULL PRIMARY KEY,
    ColorIndex      INTEGER NOT NULL,
    LocationId      INTEGER NOT NULL,
    StyleIndex      INTEGER NOT NULL,
    UserMarkGuid    TEXT NOT NULL UNIQUE,
    Version         INTEGER NOT NULL,
    FOREIGN KEY(LocationId) REFERENCES Location(LocationId)
);



-- BlockRange definition

CREATE TABLE BlockRange ( BlockRangeId    INTEGER NOT NULL PRIMARY KEY, BlockType       INTEGER NOT NULL, Identifier      INTEGER NOT NULL, StartToken      INTEGER, EndToken        INTEGER, UserMarkId      INTEGER NOT NULL, CHECK (BlockType BETWEEN 1 AND 2), FOREIGN KEY(UserMarkId) REFERENCES UserMark(UserMarkId) );



-- Note definition

CREATE TABLE "Note"(
	NoteId           INTEGER NOT NULL PRIMARY KEY,
	Guid             TEXT NOT NULL UNIQUE,
	UserMarkId       INTEGER,
	LocationId       INTEGER,
	Title            TEXT, 
	Content          TEXT,
	LastModified     TEXT NOT NULL DEFAULT(strftime('%Y-%m-%dT%H:%M:%SZ', 'now')),
	Created          TEXT NOT NULL DEFAULT(strftime('%Y-%m-%dT%H:%M:%SZ', 'now')),
	BlockType        INTEGER NOT NULL DEFAULT 0,
	BlockIdentifier  INTEGER,
	FOREIGN KEY(UserMarkId) REFERENCES UserMark(UserMarkId),
	FOREIGN KEY(LocationId) REFERENCES Location(LocationId));



-- TagMap definition

CREATE TABLE "TagMap" (
    TagMapId          INTEGER NOT NULL PRIMARY KEY,
    PlaylistItemId    INTEGER,
    LocationId        INTEGER,
    NoteId            INTEGER,
    TagId             INTEGER NOT NULL,
    Position          INTEGER NOT NULL,
    FOREIGN KEY(TagId) REFERENCES Tag(TagId),
    FOREIGN KEY(PlaylistItemId) REFERENCES PlaylistItem(PlaylistItemId),
    FOREIGN KEY(LocationId) REFERENCES Location(LocationId),
    FOREIGN KEY(NoteId) REFERENCES Note(NoteId),
    CONSTRAINT TagId_Position UNIQUE(TagId, Position),
    CONSTRAINT TagId_NoteId UNIQUE(TagId, NoteId),
    CONSTRAINT TagId_LocationId UNIQUE(TagId, LocationId),
);
